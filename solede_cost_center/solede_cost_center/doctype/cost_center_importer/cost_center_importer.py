# Copyright (c) 2025, Solede SA and contributors
# For license information, please see license.txt

import csv
from functools import reduce

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, cstr
from frappe.utils.xlsxutils import (
	read_xls_file_from_attached_file,
	read_xlsx_file_from_attached_file,
)


class CostCenterImporter(Document):
	def validate(self):
		if self.import_file:
			get_cost_centers(
				"Cost Center Importer", "All Cost Centers", file_name=self.import_file, for_validate=1
			)


def get_file(file_name):
	"""Get file document and validate extension"""
	file_doc = frappe.get_doc("File", {"file_url": file_name})
	parts = file_doc.get_extension()
	extension = parts[1].lstrip(".")

	if extension not in ("csv", "xlsx", "xls"):
		frappe.throw(
			_("Only CSV and Excel files can be used for importing data. Please check the file format.")
		)

	return file_doc, extension


def generate_data_from_csv(file_doc, as_dict=False):
	"""Read CSV file and return data"""
	file_path = file_doc.get_full_path()

	data = []
	with open(file_path, encoding="utf-8") as in_file:
		csv_reader = list(csv.reader(in_file))
		headers = csv_reader[0]
		del csv_reader[0]

		for row in csv_reader:
			if as_dict:
				data.append({frappe.scrub(header): row[index] for index, header in enumerate(headers)})
			else:
				data.append(row)

	return data


def generate_data_from_excel(file_doc, extension, as_dict=False):
	"""Read Excel file and return data"""
	content = file_doc.get_content()

	if extension == "xlsx":
		rows = read_xlsx_file_from_attached_file(fcontent=content)
	elif extension == "xls":
		rows = read_xls_file_from_attached_file(content)

	data = []
	headers = rows[0]
	del rows[0]

	for row in rows:
		if as_dict:
			data.append({frappe.scrub(header): row[index] for index, header in enumerate(headers)})
		else:
			data.append(row)

	return data


def validate_columns(data):
	"""Validate that data has correct number of columns"""
	if not data:
		frappe.throw(_("No data found. The file appears to be empty."))

	no_of_columns = max([len(d) for d in data])

	if no_of_columns != 4:
		frappe.throw(
			_(
				"Expected 4 columns (ID, Cost Center Name, Parent Cost Center, Is Group). "
				"Found {0} columns. Please check the template."
			).format(no_of_columns),
			title=_("Wrong Template"),
		)


@frappe.whitelist()
def validate_company(company):
	"""Check if company has GL entries with cost centers"""
	gl_entries_count = frappe.db.count("GL Entry", {"company": company, "cost_center": ["is", "set"]})
	if gl_entries_count > 0:
		return {"has_gl_entries": True, "count": gl_entries_count}
	return {"has_gl_entries": False, "count": 0}


def delete_gl_entries_with_cost_center(company):
	"""Delete all GL Entries with Cost Centers for the company"""
	gl_entries = frappe.get_all(
		"GL Entry",
		filters={"company": company, "cost_center": ["is", "set"]},
		pluck="name"
	)

	for gl_entry in gl_entries:
		frappe.delete_doc("GL Entry", gl_entry, ignore_permissions=True, force=True)

	frappe.db.commit()
	return len(gl_entries)


def build_forest(data):
	"""
	Convert list of rows into a nested tree structure.
	Each row: [id, cost_center_name, parent_cost_center_id, is_group]
	"""

	def set_nested(d, path, value):
		reduce(lambda d, k: d.setdefault(k, {}), path[:-1], d)[path[-1]] = value
		return d

	def return_parent(data, child_id):
		"""Return the path from root to child"""
		for row in data:
			row_id, cost_center_name, parent_id, is_group = row[0:4]
			row_id = cstr(row_id).strip()
			parent_id = cstr(parent_id).strip() if parent_id else ""

			if row_id == child_id:
				if not parent_id or parent_id == row_id:
					return [row_id]
				else:
					parent_path = return_parent(data, parent_id)
					if not parent_path:
						frappe.throw(
							_("Parent Cost Center with ID {0} does not exist in the file").format(
								frappe.bold(parent_id)
							)
						)
					return [child_id, *parent_path]
		return None

	cost_centers_map = {}
	paths = []
	line_no = 2
	error_messages = []

	for row in data:
		if len(row) < 4:
			error_messages.append(_("Row {0}: Expected 4 columns, found {1}").format(line_no, len(row)))
			line_no += 1
			continue

		row_id, cost_center_name, parent_id, is_group = row[0:4]

		row_id = cstr(row_id).strip()
		cost_center_name = cstr(cost_center_name).strip()
		parent_id = cstr(parent_id).strip() if parent_id else ""
		is_group = cint(is_group)

		if not row_id:
			error_messages.append(_("Row {0}: ID is required").format(line_no))
			line_no += 1
			continue

		if not cost_center_name:
			error_messages.append(_("Row {0}: Cost Center Name is required").format(line_no))
			line_no += 1
			continue

		cost_centers_map[row_id] = {
			"cost_center_name": cost_center_name,
			"custom_id": row_id,
		}
		if is_group:
			cost_centers_map[row_id]["is_group"] = 1

		path = return_parent(data, row_id)
		if path:
			paths.append(path[::-1])

		line_no += 1

	if error_messages:
		frappe.throw("<br>".join(error_messages))

	out = {}
	for path in paths:
		for n, cc_id in enumerate(path):
			set_nested(out, path[: n + 1], cost_centers_map[cc_id])

	return out


@frappe.whitelist()
def get_cost_centers(doctype, parent, is_root=False, file_name=None, for_validate=0):
	"""Called by tree view to fetch node's children"""

	file_doc, extension = get_file(file_name)
	parent = None if parent == _("All Cost Centers") else parent

	if extension == "csv":
		data = generate_data_from_csv(file_doc)
	else:
		data = generate_data_from_excel(file_doc, extension)

	validate_columns(data)

	if not for_validate:
		forest = build_forest(data)
		cost_centers = build_tree_from_forest("", chart_data=forest)

		# Filter to show data for the selected node only
		# Root nodes have parent_cost_center = "" while parent is None for "All Cost Centers"
		if parent is None:
			cost_centers = [d for d in cost_centers if not d.get("parent_cost_center")]
		else:
			cost_centers = [d for d in cost_centers if d.get("parent_cost_center") == parent]

		return cost_centers
	else:
		return {"show_import_button": 1}


def build_tree_from_forest(parent, chart_data):
	"""Build a flat list of cost centers for tree rendering"""
	result = []

	for key, value in chart_data.items():
		is_group = value.get("is_group", 0)
		cost_center_name = value.get("cost_center_name", key)
		custom_id = value.get("custom_id", key)

		node = {
			"value": custom_id,
			"title": cost_center_name,
			"parent_cost_center": parent,
			"expandable": is_group,
			"is_group": is_group,
			"custom_id": custom_id,
		}
		result.append(node)

		# Recursively process children
		children = {k: v for k, v in value.items() if isinstance(v, dict)}
		if children:
			result.extend(build_tree_from_forest(custom_id, children))

	return result


def unset_existing_cost_centers(company):
	"""Remove existing cost centers for the company"""
	# Reset Company cost center fields
	frappe.db.set_value(
		"Company",
		company,
		{
			"cost_center": "",
			"round_off_cost_center": "",
			"depreciation_cost_center": "",
		},
	)

	# Delete all Cost Centers for this company
	# Order by lft DESC to delete children before parents (nested set order)
	cost_centers = frappe.get_all(
		"Cost Center",
		filters={"company": company},
		order_by="lft desc",
		pluck="name"
	)
	for cc in cost_centers:
		frappe.delete_doc("Cost Center", cc, ignore_permissions=True, force=True)

	frappe.db.commit()


def create_cost_centers_from_forest(company, forest, parent=None):
	"""Recursively create cost centers from forest structure"""
	for key, value in forest.items():
		is_group = value.get("is_group", 0)
		cost_center_name = value.get("cost_center_name", key)
		custom_id = value.get("custom_id", key)

		# Create the cost center
		cc = frappe.new_doc("Cost Center")
		cc.cost_center_name = cost_center_name
		cc.company = company
		cc.is_group = is_group
		cc.parent_cost_center = parent
		cc.custom_id = custom_id
		# Skip validation for root node (ERPNext requires root name = company name)
		cc.flags.ignore_mandatory = True
		if not parent:
			cc.flags.ignore_validate = True
		cc.insert(ignore_permissions=True)

		# Recursively create children
		children = {k: v for k, v in value.items() if isinstance(v, dict)}
		if children:
			create_cost_centers_from_forest(company, children, parent=cc.name)


def set_default_cost_center(company):
	"""Set the root cost center as default for the company"""
	root_cost_center = frappe.db.get_value(
		"Cost Center", {"company": company, "parent_cost_center": ["is", "not set"]}, "name"
	)

	if root_cost_center:
		frappe.db.set_value("Company", company, "cost_center", root_cost_center)


@frappe.whitelist()
def import_cost_centers(file_name, company, force_delete_gl_entries=0):
	"""Main import function"""
	force_delete_gl_entries = cint(force_delete_gl_entries)

	# Check for GL entries with cost centers
	validation = validate_company(company)
	if validation.get("has_gl_entries"):
		if force_delete_gl_entries:
			deleted_count = delete_gl_entries_with_cost_center(company)
			frappe.msgprint(
				_("Deleted {0} GL Entries with Cost Centers").format(deleted_count),
				indicator="orange",
				alert=True
			)
		else:
			frappe.throw(
				_(
					"Cannot import Cost Centers. {0} GL Entries with Cost Centers exist for this company. "
					"Enable 'Force Delete GL Entries' to delete them."
				).format(validation.get("count"))
			)

	# Delete existing cost centers
	unset_existing_cost_centers(company)

	# Read file
	file_doc, extension = get_file(file_name)

	if extension == "csv":
		data = generate_data_from_csv(file_doc)
	else:
		data = generate_data_from_excel(file_doc, extension)

	validate_columns(data)

	# Build forest and create cost centers
	forest = build_forest(data)
	create_cost_centers_from_forest(company, forest)

	# Set default cost center
	set_default_cost_center(company)

	frappe.db.commit()

	return {"success": True, "message": _("Cost Centers imported successfully")}


@frappe.whitelist()
def download_template(file_type):
	"""Download CSV/Excel template"""
	from frappe.utils.csvutils import UnicodeWriter

	fields = ["ID", "Cost Center Name", "Parent Cost Center", "Is Group"]
	writer = UnicodeWriter()
	writer.writerow(fields)

	# Add sample rows
	writer.writerow(["ROOT001", "Main Cost Center", "", "1"])
	writer.writerow(["SALES001", "Sales", "ROOT001", "1"])
	writer.writerow(["SALES-IT", "Sales Italy", "SALES001", "0"])
	writer.writerow(["SALES-EU", "Sales Europe", "SALES001", "0"])
	writer.writerow(["ADMIN001", "Administration", "ROOT001", "0"])

	if file_type == "CSV":
		frappe.response["result"] = cstr(writer.getvalue())
		frappe.response["type"] = "csv"
		frappe.response["doctype"] = "Cost Center Importer"
	else:
		# Excel
		import csv
		import os

		from frappe.utils.xlsxutils import make_xlsx

		filename = frappe.generate_hash("", 10)
		with open(filename, "wb") as f:
			f.write(cstr(writer.getvalue()).encode("utf-8"))
		f = open(filename)
		reader = csv.reader(f)

		xlsx_file = make_xlsx(reader, "Cost Center Importer Template")

		f.close()
		os.remove(filename)

		frappe.response["filename"] = "cost_center_importer_template.xlsx"
		frappe.response["filecontent"] = xlsx_file.getvalue()
		frappe.response["type"] = "binary"
