from erpnext.accounts.doctype.cost_center.cost_center import CostCenter


class CustomCostCenter(CostCenter):
	def autoname(self):
		# Se custom_id e valorizzato, usa quello come name
		if self.get("custom_id"):
			self.name = self.custom_id
		else:
			# Comportamento originale di ERPNext
			super().autoname()
