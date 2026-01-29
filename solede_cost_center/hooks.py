app_name = "solede_cost_center"
app_title = "Solede Cost Center"
app_publisher = "Solede SA"
app_description = "Import Cost Centers from CSV/Excel with custom naming support"
app_email = "info@solede.com"
app_license = "agpl-3.0"

required_apps = ["erpnext"]

# DocType Class Override
override_doctype_class = {
	"Cost Center": "solede_cost_center.overrides.cost_center.CustomCostCenter"
}

# Fixtures
fixtures = [
	{
		"dt": "Custom Field",
		"filters": [["name", "in", ["Cost Center-custom_id"]]]
	},
	{
		"dt": "Property Setter",
		"filters": [["doc_type", "=", "Cost Center"], ["module", "=", "Solede Cost Center"]]
	}
]
