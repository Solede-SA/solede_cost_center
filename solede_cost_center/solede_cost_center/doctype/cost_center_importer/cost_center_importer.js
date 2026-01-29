// Copyright (c) 2025, Solede SA and contributors
// For license information, please see license.txt

frappe.ui.form.on("Cost Center Importer", {
	onload: function (frm) {
		frm.set_value("company", "");
		frm.set_value("import_file", "");
		frm.set_value("force_delete_gl_entries", 0);
	},

	refresh: function (frm) {
		// Disable default save
		frm.disable_save();

		// Show/hide sections based on company selection
		frm.set_df_property("import_file_section", "hidden", frm.doc.company ? 0 : 1);

		if (frm.doc.import_file) {
			frappe.run_serially([
				() => generate_tree_preview(frm),
				() => create_import_button(frm),
				() => frm.set_df_property("chart_preview", "hidden", 0),
			]);
		}

		frm.set_df_property(
			"chart_preview",
			"hidden",
			$(frm.fields_dict["chart_tree"].wrapper).html() != "" ? 0 : 1
		);
	},

	download_template: function (frm) {
		var d = new frappe.ui.Dialog({
			title: __("Download Template"),
			fields: [
				{
					label: "File Type",
					fieldname: "file_type",
					fieldtype: "Select",
					reqd: 1,
					options: ["Excel", "CSV"],
				},
			],
			primary_action: function () {
				let data = d.get_values();

				open_url_post(
					"/api/method/solede_cost_center.solede_cost_center.doctype.cost_center_importer.cost_center_importer.download_template",
					{
						file_type: data.file_type,
					}
				);

				d.hide();
			},
			primary_action_label: __("Download"),
		});
		d.show();
	},

	import_file: function (frm) {
		if (!frm.doc.import_file) {
			frm.page.set_indicator("");
			frm.page.clear_primary_action();
			$(frm.fields_dict["chart_tree"].wrapper).empty();
			frm.set_df_property("chart_preview", "hidden", 1);
		} else {
			frm.trigger("refresh");
		}
	},

	company: function (frm) {
		// Reset force delete when company changes
		frm.set_value("force_delete_gl_entries", 0);
		frm.set_df_property("force_delete_gl_entries", "hidden", 1);

		if (frm.doc.company) {
			// Check if GL Entries with cost center exist for the company
			frappe.call({
				method: "solede_cost_center.solede_cost_center.doctype.cost_center_importer.cost_center_importer.validate_company",
				args: {
					company: frm.doc.company,
				},
				callback: function (r) {
					if (r.message && r.message.has_gl_entries) {
						// Show warning and force delete checkbox
						frm.set_df_property("force_delete_gl_entries", "hidden", 0);
						frappe.msgprint({
							title: __("Warning"),
							indicator: "orange",
							message: __(
								"{0} GL Entries with Cost Centers exist for this company. " +
									"To proceed with import, you must enable 'Force Delete GL Entries' " +
									"which will permanently delete these transactions.",
								[r.message.count]
							),
						});
					} else {
						frm.set_df_property("force_delete_gl_entries", "hidden", 1);
					}
					frm.trigger("refresh");
				},
			});
		}
	},
});

var create_import_button = function (frm) {
	frm.page
		.set_primary_action(__("Import"), function () {
			let confirm_msg = __(
				"This will delete ALL existing Cost Centers for company {0} and create new ones from the file.",
				[frm.doc.company]
			);

			if (frm.doc.force_delete_gl_entries) {
				confirm_msg +=
					" " +
					__(
						"WARNING: All GL Entries with Cost Centers will also be permanently deleted!"
					);
			}

			confirm_msg += " " + __("Continue?");

			frappe.confirm(confirm_msg, function () {
				return frappe.call({
					method: "solede_cost_center.solede_cost_center.doctype.cost_center_importer.cost_center_importer.import_cost_centers",
					args: {
						file_name: frm.doc.import_file,
						company: frm.doc.company,
						force_delete_gl_entries: frm.doc.force_delete_gl_entries,
					},
					freeze: true,
					freeze_message: __("Creating Cost Centers..."),
					callback: function (r) {
						if (!r.exc) {
							frm.page.set_indicator(__("Import Successful"), "blue");
							frappe.show_alert({
								message: __("Cost Centers imported successfully"),
								indicator: "green",
							});
							create_reset_button(frm);
						}
					},
				});
			});
		})
		.addClass("btn btn-primary");
};

var create_reset_button = function (frm) {
	frm.page
		.set_primary_action(__("Reset"), function () {
			frm.page.clear_primary_action();
			frm.reload_doc();
		})
		.addClass("btn btn-primary");
};

var generate_tree_preview = function (frm) {
	let parent = __("All Cost Centers");
	$(frm.fields_dict["chart_tree"].wrapper).empty();

	// Generate tree structure based on the file data
	return new frappe.ui.Tree({
		parent: $(frm.fields_dict["chart_tree"].wrapper),
		label: parent,
		expandable: true,
		method:
			"solede_cost_center.solede_cost_center.doctype.cost_center_importer.cost_center_importer.get_cost_centers",
		args: {
			file_name: frm.doc.import_file,
			parent: parent,
			doctype: "Cost Center Importer",
		},
		onclick: function (node) {
			// Nothing on click for now
		},
	});
};
