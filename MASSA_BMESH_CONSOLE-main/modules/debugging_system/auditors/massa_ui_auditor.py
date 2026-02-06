def audit_mesh(obj, op_class=None):
    auditor = Massa_UI_Auditor(op_class)
    report = auditor.run_scan()
    # The runner expects a list of error strings
    return report["flags"]

class Massa_UI_Auditor:
    def __init__(self, op_class):
        self.op_class = op_class
        self.report = {"status": "PASS", "flags": [], "visible_params": []}

    def run_scan(self):
        # 0. Context Check
        if not self.op_class:
             # It's optional for standard audits, but we can't run UI checks without it
             return self.report

        # 1. Option Check
        if not hasattr(self.op_class, "bl_options"):
             self.report["flags"].append("CRITICAL_MISSING_BL_OPTIONS")
             self.report["status"] = "FAIL"
             return self.report
        else:
            if "UNDO" not in self.op_class.bl_options:
                self.report["flags"].append("CRITICAL_UI_NO_UNDO_FLAG")
                self.report["status"] = "FAIL"

        # 2. RNA Check
        rna_props = []
        if hasattr(self.op_class, "bl_rna"):
            rna_props = [p.identifier for p in self.op_class.bl_rna.properties]
        elif hasattr(self.op_class, "__annotations__"):
            rna_props = list(self.op_class.__annotations__.keys())
        else:
             self.report["flags"].append("CRITICAL_CLASS_NOT_REGISTERED")
             self.report["status"] = "FAIL"
             return self.report

        ignored = {"rna_type", "bl_idname", "bl_label", "bl_description", "bl_options", "bl_undo_group", "script"}
        found = [p for p in rna_props if p not in ignored]
        # Allow standard names
        bad = [p for p in found if not p.startswith("prop_") and p not in ["width", "length", "height", "radius"]]
        
        self.report["visible_params"] = found
        if not found:
            self.report["flags"].append("CRITICAL_EMPTY_PANEL")
            self.report["status"] = "FAIL"
            
        return self.report