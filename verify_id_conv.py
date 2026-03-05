import bpy

def test_safe_conversion():
    print("\n--- Testing Safe IDProperty Conversion ---")

    # 1. Setup an object with IDProperty (PropertyGroup-like)
    obj = bpy.data.objects.new("TestObj", None)
    obj["MASSA_PARAMS"] = {"blade_count": 12, "nested": {"a": 1}}

    id_prop = obj["MASSA_PARAMS"]
    print(f"Type of MASSA_PARAMS: {type(id_prop)}")

    # Simulate the logic from the code
    params = id_prop.to_dict() if hasattr(id_prop, "to_dict") else dict(id_prop.items())

    print(f"Converted params: {params}")
    assert isinstance(params, dict), "Should be a standard dictionary"
    assert params["blade_count"] == 12, "Value should match"
    assert isinstance(params["nested"], dict), "Nested structures should also be converted to dict"
    print("Test 1 (MASSA_PARAMS) Passed!")

    # 2. Test MASSA_TEMP_RESTORE in Scene
    scene = bpy.context.scene
    scene["MASSA_TEMP_RESTORE"] = {"test_val": 42}

    id_prop_scene = scene["MASSA_TEMP_RESTORE"]
    print(f"Type of MASSA_TEMP_RESTORE: {type(id_prop_scene)}")

    restore_data = id_prop_scene.to_dict() if hasattr(id_prop_scene, "to_dict") else dict(id_prop_scene.items())

    print(f"Converted restore_data: {restore_data}")
    assert isinstance(restore_data, dict), "Should be a standard dictionary"
    assert restore_data["test_val"] == 42, "Value should match"
    print("Test 2 (MASSA_TEMP_RESTORE) Passed!")

    # 3. Test fallback (Standard Dict - shouldn't happen with Blender 5.0 props but good for robustness)
    mock_dict = {"a": 1, "b": 2}
    # Standard dict doesn't have to_dict, but has .items()
    fallback_data = mock_dict.to_dict() if hasattr(mock_dict, "to_dict") else dict(mock_dict.items())
    assert fallback_data == mock_dict
    print("Test 3 (Fallback) Passed!")

    print("--- All Safe Conversion Tests Passed! ---\n")

if __name__ == "__main__":
    try:
        test_safe_conversion()
    except Exception as e:
        print(f"Test Failed: {e}")
        exit(1)
