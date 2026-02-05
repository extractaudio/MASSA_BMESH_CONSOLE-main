import bpy

class Massa_UI_Auditor:
    def __init__(self, op_class):
        self.op_class = op_class
        self.report = {"status": "PASS", "flags": [], "visible_params": []}

    def run_scan(self):
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
        try:
            rna_props = self.op_class.bl_rna.properties
        except AttributeError:
             self.report["flags"].append("CRITICAL_CLASS_NOT_REGISTERED")
             self.report["status"] = "FAIL"
             return self.report

        ignored = {"rna_type", "bl_idname", "bl_label", "bl_description", "bl_options", "bl_undo_group", "script"}
        found = [p.identifier for p in rna_props if p.identifier not in ignored]
        bad = [p for p in found if not p.startswith("prop_")]
        
        self.report["visible_params"] = found
        if bad: self.report["flags"].append(f"WARNING_INVALID_PROP_NAMING: {bad}")
        if not found:
            self.report["flags"].append("CRITICAL_EMPTY_PANEL")
            self.report["status"] = "FAIL"
            
        return self.report