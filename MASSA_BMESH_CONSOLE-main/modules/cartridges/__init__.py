import bpy

# -------------------------------------------------------------------
# 1. CARTRIDGE IMPORTS
# -------------------------------------------------------------------
# The Architecture relies on these modules being standalone.
# They should ONLY import from '...operators.massa_base' and standard libraries.

# --- LEGACY SUITE (prim_con_*) ---
from . import prim_con_board
from . import prim_con_block
from . import prim_con_bracket
from . import prim_con_flooring
from . import prim_con_beam
from . import prim_con_pipe
from . import prim_con_truss
from . import prim_con_rebar
from . import prim_con_sheet
from . import prim_con_window
from . import prim_con_doorway
from . import prim_con_porch_decking
from . import prim_con_cabinet
from . import prim_con_house_generator

# --- CORE PRIMITIVES (cart_prim_*) ---
from . import cart_prim_rock_boulder
from . import cart_plank
from . import cart_prim_01_beam
from . import cart_prim_02_pipe
from . import cart_prim_03_corrugated
from . import cart_prim_04_panel
from . import cart_prim_05_catenary
from . import cart_prim_06_gusset
from . import cart_prim_07_louver
from . import cart_prim_08_bolt
from . import cart_prim_09_chain
from . import cart_prim_10_arch
from . import cart_prim_11_helix
from . import cart_prim_12_truss
from . import cart_prim_13_shard
from . import cart_prim_14_y_joint
from . import cart_prim_15_scale
from . import cart_prim_16_lathe
from . import cart_prim_17_canvas
from . import cart_prim_18_tank
from . import cart_prim_19_tray
from . import cart_prim_20_bundle
from . import cart_prim_21_column
from . import cart_prim_22_duct
from . import cart_prim_23_cable_tray
from . import cart_prim_24_gutter
from . import cart_crate
from . import cart_scaffolding
from . import cart_prim_landscape

# --- ARCHITECTURE SUITE (cart_arch_*) ---
from . import cart_arch_01_stairs_linear
from . import cart_arch_02_stairs_spiral
from . import cart_arch_03_stairs_industrial
from . import cart_arc_01_wall
from . import cart_arc_02_stairs
from . import cart_arc_03_window
from . import cart_arc_04_doorway
from . import cart_arc_05_column

# --- INDUSTRIAL SUITE (cart_ind_*) ---
from . import cart_ind_01_truss
from . import cart_ind_02_duct
from . import cart_ind_03_catwalk
from . import cart_ind_04_ladder
from . import cart_ind_05_silo

# --- URBAN SUITE (cart_urb_*) ---
from . import cart_urb_01_sidewalk
from . import cart_urb_02_railing
from . import cart_urb_03_streetlight
from . import cart_urb_04_barrier
from . import cart_urb_05_fence

# --- PROPS & LANDSCAPE SUITE (cart_prp_*, cart_lnd_*) ---
from . import cart_prp_01_container
from . import cart_prp_02_rack
from . import cart_prp_03_greeble
from . import cart_lnd_01_planter
from . import cart_lnd_02_boulder

# --- ASSEMBLIES & PARTS ---
from . import cart_building_assembly_1
from . import cart_building_assembly_2
from . import cart_building_assembly_3
from . import cart_walkway
from . import cart_cables
from . import cart_parts_handrail
from . import cart_arch_tiny_home
from . import cart_arch_mobile_home
from . import cart_asm_06_transit
from . import cart_asm_07_vending
from . import cart_asm_08_signage
from . import cart_asm_09_checkpoint
from . import cart_asm_10_tower


# -------------------------------------------------------------------
# 2. REGISTRY AGGREGATION
# -------------------------------------------------------------------

# List of Module Objects (Used by UI Panel to read CARTRIDGE_META)
MODULES = [
    # Legacy
    prim_con_board,
    prim_con_block,
    prim_con_bracket,
    prim_con_flooring,
    prim_con_beam,
    prim_con_pipe,
    prim_con_truss,
    prim_con_rebar,
    prim_con_sheet,
    prim_con_window,
    prim_con_doorway,
    prim_con_porch_decking,
    prim_con_cabinet,
    prim_con_house_generator,
    # Core
    cart_prim_rock_boulder,
    cart_plank,
    cart_prim_01_beam,
    cart_prim_02_pipe,
    cart_prim_03_corrugated,
    cart_prim_04_panel,
    cart_prim_05_catenary,
    cart_prim_06_gusset,
    cart_prim_07_louver,
    cart_prim_08_bolt,
    cart_prim_09_chain,
    cart_prim_10_arch,
    cart_prim_11_helix,
    cart_prim_12_truss,
    cart_prim_13_shard,
    cart_prim_14_y_joint,
    cart_prim_15_scale,
    cart_prim_16_lathe,
    cart_prim_17_canvas,
    cart_prim_18_tank,
    cart_prim_19_tray,
    cart_prim_20_bundle,
    cart_prim_21_column,
    cart_prim_22_duct,
    cart_prim_23_cable_tray,
    cart_prim_24_gutter,
    cart_crate,
    cart_scaffolding,
    cart_prim_landscape,
    # Arch
    cart_arch_01_stairs_linear,
    cart_arch_02_stairs_spiral,
    cart_arch_03_stairs_industrial,
    cart_arc_01_wall,
    cart_arc_02_stairs,
    cart_arc_03_window,
    cart_arc_04_doorway,
    cart_arc_05_column,
    # Ind
    cart_ind_01_truss,
    cart_ind_02_duct,
    cart_ind_03_catwalk,
    cart_ind_04_ladder,
    cart_ind_05_silo,
    # Urb
    cart_urb_01_sidewalk,
    cart_urb_02_railing,
    cart_urb_03_streetlight,
    cart_urb_04_barrier,
    cart_urb_05_fence,
    # Props/Land
    cart_prp_01_container,
    cart_prp_02_rack,
    cart_prp_03_greeble,
    cart_lnd_01_planter,
    cart_lnd_02_boulder,
    # Assemblies & Parts
    cart_building_assembly_1,
    cart_building_assembly_2,
    cart_building_assembly_3,
    cart_walkway,
    cart_cables,
    cart_parts_handrail,
    cart_arch_tiny_home,
    cart_arch_mobile_home,
    cart_asm_06_transit,
    cart_asm_07_vending,
    cart_asm_08_signage,
    cart_asm_09_checkpoint,
    cart_asm_10_tower,
]

# List of Operator Classes (Used for Registration)
CLASSES = [
    # Legacy
    prim_con_board.MASSA_OT_prim_con_board,
    prim_con_block.MASSA_OT_prim_con_block,
    prim_con_bracket.MASSA_OT_prim_con_bracket,
    prim_con_flooring.MASSA_OT_prim_con_flooring,
    prim_con_beam.MASSA_OT_prim_con_beam,
    prim_con_pipe.MASSA_OT_prim_con_pipe,
    prim_con_truss.MASSA_OT_prim_con_truss,
    prim_con_rebar.MASSA_OT_prim_con_rebar,
    prim_con_sheet.MASSA_OT_prim_con_sheet,
    prim_con_window.MASSA_OT_prim_con_window,
    prim_con_doorway.MASSA_OT_prim_con_doorway,
    prim_con_porch_decking.MASSA_OT_prim_con_porch_decking,
    prim_con_cabinet.MASSA_OT_prim_con_cabinet,
    prim_con_house_generator.MASSA_OT_prim_con_house_generator,
    # Core
    cart_prim_rock_boulder.MASSA_OT_PrimRockBoulder,
    cart_plank.MASSA_OT_Plank,
    cart_prim_01_beam.MASSA_OT_PrimBeam,
    cart_prim_02_pipe.MASSA_OT_PrimPipe,
    cart_prim_03_corrugated.MASSA_OT_PrimCorrugated,
    cart_prim_04_panel.MASSA_OT_PrimPanel,
    cart_prim_05_catenary.MASSA_OT_PrimCatenary,
    cart_prim_06_gusset.MASSA_OT_PrimGusset,
    cart_prim_07_louver.MASSA_OT_PrimLouver,
    cart_prim_08_bolt.MASSA_OT_PrimBolt,
    cart_prim_09_chain.MASSA_OT_PrimChain,
    cart_prim_10_arch.MASSA_OT_PrimArch,
    cart_prim_11_helix.MASSA_OT_PrimHelix,
    cart_prim_12_truss.MASSA_OT_PrimTruss,
    cart_prim_13_shard.MASSA_OT_PrimShard,
    cart_prim_14_y_joint.MASSA_OT_PrimYJoint,
    cart_prim_15_scale.MASSA_OT_PrimScale,
    cart_prim_16_lathe.MASSA_OT_PrimLathe,
    cart_prim_17_canvas.MASSA_OT_PrimCanvas,
    cart_prim_18_tank.MASSA_OT_PrimTank,
    cart_prim_19_tray.MASSA_OT_PrimTray,
    cart_prim_20_bundle.MASSA_OT_PrimBundle,
    cart_prim_21_column.MASSA_OT_PrimColumn,
    cart_prim_22_duct.MASSA_OT_PrimDuct,
    cart_prim_23_cable_tray.MASSA_OT_PrimCableTray,
    cart_prim_24_gutter.MASSA_OT_PrimGutter,
    cart_crate.MASSA_OT_Crate,
    cart_scaffolding.MASSA_OT_Scaffolding,
    cart_prim_landscape.MASSA_OT_PrimLandscape,
    # Arch
    cart_arch_01_stairs_linear.MASSA_OT_ArchStairsLinear,
    cart_arch_02_stairs_spiral.MASSA_OT_ArchStairsSpiral,
    cart_arch_03_stairs_industrial.MASSA_OT_ArchStairsIndustrial,
    cart_arc_01_wall.MASSA_OT_ArcWall,
    cart_arc_02_stairs.MASSA_OT_ArcStairs,
    cart_arc_03_window.MASSA_OT_ArcWindow,
    cart_arc_04_doorway.MASSA_OT_ArcDoorway,
    cart_arc_05_column.MASSA_OT_ArcColumn,
    # Ind
    cart_ind_01_truss.MASSA_OT_IndTruss,
    cart_ind_02_duct.MASSA_OT_IndDuct,
    cart_ind_03_catwalk.MASSA_OT_IndCatwalk,
    cart_ind_04_ladder.MASSA_OT_IndLadder,
    cart_ind_05_silo.MASSA_OT_IndSilo,
    # Urb
    cart_urb_01_sidewalk.MASSA_OT_UrbSidewalk,
    cart_urb_02_railing.MASSA_OT_UrbRailing,
    cart_urb_03_streetlight.MASSA_OT_UrbStreetlight,
    cart_urb_04_barrier.MASSA_OT_UrbBarrier,
    cart_urb_05_fence.MASSA_OT_UrbFence,
    # Props/Land
    cart_prp_01_container.MASSA_OT_PrpContainer,
    cart_prp_02_rack.MASSA_OT_PrpRack,
    cart_prp_03_greeble.MASSA_OT_PrpGreeble,
    cart_lnd_01_planter.MASSA_OT_LndPlanter,
    cart_lnd_02_boulder.MASSA_OT_LndBoulder,
    # Assemblies & Parts
    cart_building_assembly_1.MASSA_OT_BuildingAssembly1,
    cart_building_assembly_2.MASSA_OT_Canopy,
    cart_building_assembly_3.MASSA_OT_BuildingAssembly3,
    cart_walkway.MASSA_OT_Walkway,
    cart_cables.MASSA_OT_Cables,
    cart_parts_handrail.MASSA_OT_PartsHandrail,
    cart_arch_tiny_home.MASSA_OT_ArchTinyHome,
    cart_arch_mobile_home.MASSA_OT_ArchMobileHome,
    cart_asm_06_transit.MASSA_OT_AsmTransit,
    cart_asm_07_vending.MASSA_OT_AsmVending,
    cart_asm_08_signage.MASSA_OT_AsmSignage,
    cart_asm_09_checkpoint.MASSA_OT_AsmCheckpoint,
    cart_asm_10_tower.MASSA_OT_AsmTower,
]

# -------------------------------------------------------------------
# 3. REGISTRATION HANDLERS
# -------------------------------------------------------------------


def register():
    # print("Massa: Registering Cartridges...")
    for cls in CLASSES:
        try:
            bpy.utils.register_class(cls)
        except ValueError:
            pass  # Already registered
        except RuntimeError as e:
            print(f"Massa Error: Could not register {cls.__name__}: {e}")


def unregister():
    # print("Massa: Unregistering Cartridges...")
    for cls in reversed(CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass
