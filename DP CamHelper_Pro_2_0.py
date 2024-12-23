bl_info = {
    "name": "DP Cam Helper Pro",
    "author": "Dimona Patrick",
    "company": "digital pixels forge",
    "version": (2, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Cam Helper Pro",
    "description": "Extended camera management tools for viewport",
    "category": "3D View",
}


import bpy
import math
import os
import wave
import array
import math
from statistics import mean
from mathutils import Vector, Matrix, Quaternion
from bpy.types import UIList
from bpy.types import (Panel, Operator, PropertyGroup, Menu, AddonPreferences)
from bpy.props import (FloatProperty, BoolProperty, IntProperty, 
                      EnumProperty, StringProperty, FloatVectorProperty, PointerProperty, CollectionProperty)
					  
#utils/fonctions
def analyze_audio_simple(file_path, chunk_size=2048, threshold=0.6):
    with wave.open(file_path, 'rb') as wf:
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        n_frames = wf.getnframes()
        
        # Read raw data
        raw_data = wf.readframes(n_frames)
        
        # Convert raw data to array of integers
        if sampwidth == 2:
            data = array.array('h', raw_data)
        else:
            data = array.array('i', raw_data)
            
        # Process only one channel if stereo
        if n_channels == 2:
            data = data[::2]
        
        # Find beats
        beats = []
        current_frame = 0
        window_size = chunk_size
        
        while current_frame < len(data) - window_size:
            window = data[current_frame:current_frame + window_size]
            
            # Calculate amplitude
            amplitude = sum(abs(x) for x in window) / window_size
            
            # If amplitude exceeds threshold, mark as beat
            if amplitude > threshold * 32767:  # 32767 is max value for 16-bit audio
                frame_time = current_frame / framerate
                frame_number = int(frame_time * bpy.context.scene.render.fps)
                beats.append(frame_number)
                current_frame += window_size  # Skip to avoid multiple detections
            else:
                current_frame += window_size // 2
                
        return beats
		
def update_passepartout(self, context):
    # Get active camera and selected cameras
    selected_cameras = [obj for obj in context.selected_objects if obj.type == 'CAMERA']
    active_camera = context.scene.camera
    
    # If no cameras are selected, use active camera
    if not selected_cameras and active_camera:
        selected_cameras = [active_camera]
    
    # Update passepartout for all selected cameras
    for cam_obj in selected_cameras:
        cam_data = cam_obj.data
        cam_data.show_passepartout = True
        cam_data.passepartout_alpha = self.passepartout_alpha
        
def update_camera_display_settings(self, context):
    selected_cameras = [obj for obj in context.selected_objects if obj.type == 'CAMERA']
    active_camera = context.scene.camera
    
    if not selected_cameras and active_camera:
        selected_cameras = [active_camera]
    
    for cam_obj in selected_cameras:
        cam_data = cam_obj.data
        # Update composition guides
        cam_data.show_composition_guides = self.show_composition_guides
        cam_data.show_composition_thirds = (self.guide_type == 'THIRDS')
        cam_data.show_composition_center = (self.guide_type == 'CENTER')
        cam_data.show_composition_golden = (self.guide_type == 'GOLDEN')
        cam_data.show_composition_golden_tria_a = (self.guide_type == 'GOLDEN_TRI')
        
        # Update safe areas
        cam_data.show_safe_areas = self.show_safe_areas
        if hasattr(context.scene, 'safe_areas'):
            context.scene.safe_areas.title[0] = self.safe_area_percentage
            context.scene.safe_areas.title[1] = self.safe_area_percentage
            context.scene.safe_areas.action[0] = self.safe_area_percentage
            context.scene.safe_areas.action[1] = self.safe_area_percentage
		
class CameraListProperties(PropertyGroup):
    name: StringProperty(default="")
    
class CameraListItem(PropertyGroup):
    name: StringProperty(name="Name")
    camera: PointerProperty(
        type=bpy.types.Object,
        poll=lambda self, object: object.type == 'CAMERA'
    )


# Camera List Properties
class CameraCollection(PropertyGroup):
    name: StringProperty(default="")
    camera: PointerProperty(
        type=bpy.types.Object,
        poll=lambda self, object: object.type == 'CAMERA'
    )		
		
class CamHelperProperties(PropertyGroup):
    camera_list: CollectionProperty(type=CameraListItem)
    camera_list_index: IntProperty(name="Camera Index")
    camera_collection: CollectionProperty(
        type=CameraCollection,
        name="Camera Collection"
    )
    passepartout_alpha: FloatProperty(
        name="Passepartout Opacity",
        description="Opacity of camera passepartout (0 = transparent, 1 = solid)",
        default=1.0,
        min=0.0,
        max=1.0,
        subtype='FACTOR',
        update=update_passepartout 
    )
    binding_distance: FloatProperty(
        name="Binding Distance",
        description="Distance between bound cameras",
        default=2.0,
        min=0.1,
        soft_max=10.0,
        unit='LENGTH'
    )
    
    binding_type: EnumProperty(
        name="Binding Type",
        items=[
            ('LINEAR', "Linear", "Linear path between cameras"),
            ('CIRCULAR', "Circular", "Circular path around target"),
            ('ARRAY', "Array", "Array of cameras"),
            ('ORBIT', "Orbit", "Orbital arrangement of cameras")
        ],
        default='LINEAR'
    )
    
    array_count: IntProperty(
        name="Count",
        description="Number of cameras in array",
        default=3,
        min=2,
        max=10
    )
    
    orbit_radius: FloatProperty(
        name="Orbit Radius",
        description="Radius of orbital arrangement",
        default=5.0,
        min=0.1,
        unit='LENGTH'
    )
    
    show_composition_guides: BoolProperty(
        name="Show Composition Guides",
        description="Show composition guides in camera view",
        default=False,
        update=update_camera_display_settings
    )
    
    guide_type: EnumProperty(
        name="Guide Type",
        description="Type of composition guide",
        items=[
            ('THIRDS', "Rule of Thirds", ""),
            ('GOLDEN', "Golden Ratio", ""),
            ('CENTER', "Center", ""),
            ('DIAGONAL', "Diagonal", ""),
            ('GOLDEN_TRI', "Golden Triangle", ""),
        ],
        default='THIRDS',
        update=update_camera_display_settings
    )

    dof_focus_distance: FloatProperty(
        name="Focus Distance",
        description="Distance to focus point",
        default=10.0,
        min=0.0,
        unit='LENGTH'
    )
    
    dof_aperture: FloatProperty(
        name="F-Stop",
        description="Depth of Field F-Stop number",
        default=1.4,
        min=0.95,
        max=128.0
    )

    
    show_safe_areas: BoolProperty(
        name="Show Safe Areas",
        description="Display safe areas in camera view",
        default=False,
        update=update_camera_display_settings
    )
    
    safe_area_percentage: FloatProperty(
        name="Safe Area",
        description="Percentage of safe area",
        default=0.9,
        min=0.0,
        max=1.0,
        update=update_camera_display_settings
    )
    
    lock_camera_rotation: BoolProperty(
        name="Lock Camera Rotation",
        description="Prevent camera rotation",
        default=False
    )
    
    show_camera_path: BoolProperty(
        name="Show Camera Path",
        description="Display camera motion path",
        default=False
    )
    
    camera_path_frames: IntProperty(
        name="Path Frames",
        description="Number of frames to show in camera path",
        default=100,
        min=1
    )

    # Animation Controls
    animation_speed: FloatProperty(
        name="Animation Speed",
        description="Speed multiplier for camera animations",
        default=1.0,
        min=0.1,
        max=10.0
    )

    smooth_transition: BoolProperty(
        name="Smooth Transitions",
        description="Enable smooth transitions between camera positions",
        default=True
    )

    transition_duration: IntProperty(
        name="Transition Duration",
        description="Duration of smooth transitions in frames",
        default=20,
        min=1,
        max=250
    )

    # Camera Shake
    enable_camera_shake: BoolProperty(
        name="Enable Camera Shake",
        description="Add procedural camera shake",
        default=False
    )

    shake_strength: FloatProperty(
        name="Shake Strength",
        description="Strength of camera shake",
        default=0.1,
        min=0.0,
        max=1.0
    )

    shake_frequency: FloatProperty(
        name="Shake Frequency",
        description="Frequency of camera shake",
        default=1.0,
        min=0.1,
        max=10.0
    )
    
    # Camera Path
    path_type: EnumProperty(
        name="Path Type",
        items=[
            ('BEZIER', "Bezier", "Smooth bezier curve path"),
            ('LINEAR', "Linear", "Straight line segments"),
            ('CIRCULAR', "Circular", "Circular path")
        ],
        default='BEZIER'
    )
    
    path_frames: IntProperty(
        name="Path Frames",
        description="Number of frames for camera path animation",
        default=100,
        min=1
    )
    
    # Camera Effects
    use_dolly_zoom: BoolProperty(
        name="Dolly Zoom",
        description="Enable dolly zoom effect",
        default=False
    )
    
    dolly_zoom_strength: FloatProperty(
        name="Dolly Strength",
        description="Strength of dolly zoom effect",
        default=1.0,
        min=0.1,
        max=5.0
    )
    
    # Camera Roll
    enable_roll: BoolProperty(
        name="Enable Roll",
        description="Enable camera roll animation",
        default=False
    )
    
    roll_angle: FloatProperty(
        name="Roll Angle",
        description="Camera roll angle in degrees",
        default=0.0,
        min=-180.0,
        max=180.0,
        subtype='ANGLE'
    )

    # Multi-Camera Management
    active_camera_group: StringProperty(
        name="Camera Group",
        description="Active camera group name",
        default="Main_Cam"
    )

    # Viewport Display
    show_camera_names: BoolProperty(
        name="Show Camera Names",
        description="Display camera names in viewport",
        default=True
    )

    camera_display_size: FloatProperty(
        name="Display Size",
        description="Size of camera objects in viewport",
        default=1.0,
        min=0.1,
        max=5.0
    )

class BeatAnalyzerProperties(PropertyGroup):
    audio_file: StringProperty(
        name="Audio File",
        description="Select audio file to analyze (WAV format)",
        default="",
        subtype='FILE_PATH'
    )
    
    chunk_size: IntProperty(
        name="Chunk Size",
        description="Size of audio chunks to analyze (lower = more sensitive)",
        default=2048,
        min=512,
        max=8192
    )
    
    threshold: FloatProperty(
        name="Threshold",
        description="Beat detection threshold (lower = more beats detected)",
        default=0.6,
        min=0.1,
        max=1.0
    )
    
    clear_existing: BoolProperty(
        name="Clear Existing",
        description="Clear existing beat markers before creating new ones",
        default=True
    )

    marker_prefix: StringProperty(
        name="Marker Prefix",
        description="Prefix for marker names",
        default="Beat_"
    )

class BEATANALYZER_OT_analyze_audio(Operator):
    bl_idname = "beatanalyzer.analyze_audio"
    bl_label = "Analyze Audio"
    bl_description = "Analyze audio file and detect beats"
    
    @classmethod
    def poll(cls, context):
        return context.scene is not None
    
    def analyze_audio_simple(self, file_path, chunk_size=2048, threshold=0.6):
        try:
            with wave.open(file_path, 'rb') as wf:
                n_channels = wf.getnchannels()
                sampwidth = wf.getsampwidth()
                framerate = wf.getframerate()
                n_frames = wf.getnframes()
                
                raw_data = wf.readframes(n_frames)
                
                if sampwidth == 2:
                    data = array.array('h', raw_data)
                else:
                    data = array.array('i', raw_data)
                    
                if n_channels == 2:
                    data = data[::2]
                
                beats = []
                current_frame = 0
                window_size = chunk_size
                
                while current_frame < len(data) - window_size:
                    window = data[current_frame:current_frame + window_size]
                    amplitude = sum(abs(x) for x in window) / window_size
                    
                    if amplitude > threshold * 32767:
                        frame_time = current_frame / framerate
                        frame_number = int(frame_time * bpy.context.scene.render.fps)
                        beats.append(frame_number)
                        current_frame += window_size
                    else:
                        current_frame += window_size // 2
                        
                return beats
                
        except Exception as e:
            self.report({'ERROR'}, f"Error analyzing audio: {str(e)}")
            return None
    
    def create_markers(self, context, beat_frames):
        props = context.scene.beat_analyzer_props
        
        if props.clear_existing:
            for marker in context.scene.timeline_markers:
                if marker.name.startswith(props.marker_prefix):
                    context.scene.timeline_markers.remove(marker)
        
        for i, frame in enumerate(beat_frames):
            marker = context.scene.timeline_markers.new(f"{props.marker_prefix}{i+1}", frame=frame)
            #marker.color = tuple(props.marker_color)
    
    def execute(self, context):
        props = context.scene.beat_analyzer_props
        
        if not props.audio_file:
            self.report({'ERROR'}, "No audio file selected")
            return {'CANCELLED'}
        
        filepath = bpy.path.abspath(props.audio_file)
        if not filepath.lower().endswith('.wav'):
            self.report({'ERROR'}, "Only WAV files are supported")
            return {'CANCELLED'}
        
        if not os.path.exists(filepath):
            self.report({'ERROR'}, "Audio file not found")
            return {'CANCELLED'}
        
        beat_frames = self.analyze_audio_simple(
            filepath,
            chunk_size=props.chunk_size,
            threshold=props.threshold
        )
        
        if beat_frames is None:
            return {'CANCELLED'}
        
        if len(beat_frames) == 0:
            self.report({'WARNING'}, "No beats detected. Try adjusting the threshold")
            return {'CANCELLED'}
        
        self.create_markers(context, beat_frames)
        
        self.report({'INFO'}, f"Created {len(beat_frames)} beat markers")
        return {'FINISHED'}  
        
class CAMHELPER_OT_update_passepartout(Operator):
    bl_idname = "camhelper.update_passepartout"
    bl_label = "Update Passepartout"
    bl_description = "Update passepartout settings for selected cameras"
    
    def execute(self, context):
        active_obj = context.active_object
        if active_obj and active_obj.type == 'CAMERA':
            active_obj.data.show_passepartout = True
            active_obj.data.passepartout_alpha = context.scene.cam_helper_props.passepartout_alpha
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "No active camera selected")
            return {'CANCELLED'}

class CAMHELPER_OT_add_camera_shake(Operator):
    """Add camera shake effect"""
    bl_idname = "camera_helper.add_shake"
    bl_label = "Add Camera Shake"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        camera = scene.camera
        effects = scene.camera_effects

        if not camera:
            self.report({'ERROR'}, "No active camera")
            return {'CANCELLED'}

        # Store original transform
        orig_loc = camera.location.copy()
        
        frame_start = scene.frame_start
        frame_end = scene.frame_end
        frames = frame_end - frame_start

        # Apply shake
        for frame in range(frames):
            scene.frame_set(frame + frame_start)
            
            # Calculate shake amount with decay
            decay = 1.0 - (frame / frames) * effects.shake_decay
            amplitude = effects.shake_amplitude * decay

            if effects.shake_noise_type == 'PERLIN':
                offset = Vector((
                    generate_noise(frame * effects.shake_frequency) * amplitude,
                    generate_noise((frame + 1000) * effects.shake_frequency) * amplitude,
                    generate_noise((frame + 2000) * effects.shake_frequency) * amplitude
                ))
            elif effects.shake_noise_type == 'RANDOM':
                offset = Vector((
                    random.uniform(-amplitude, amplitude),
                    random.uniform(-amplitude, amplitude),
                    random.uniform(-amplitude, amplitude)
                ))
            else:  # SINE
                t = frame * effects.shake_frequency
                offset = Vector((
                    math.sin(t) * amplitude,
                    math.cos(t) * amplitude,
                    math.sin(t * 0.5) * amplitude
                ))

            camera.location = orig_loc + offset
            camera.keyframe_insert(data_path="location", frame=frame + frame_start)

        return {'FINISHED'}

class CAMHELPER_OT_clear_camera_shake(Operator):
    bl_idname = "camhelper.clear_camera_shake"
    bl_label = "Clear Camera Shake"
    
    def execute(self, context):
        active_cam = context.scene.camera
        if not active_cam or not active_cam.animation_data:
            return {'CANCELLED'}
            
        active_cam.animation_data.drivers.clear()
        self.report({'INFO'}, "Camera shake removed")
        return {'FINISHED'}            

class CAMHELPER_PT_camera_effects(Panel):
    bl_label = "Camera Effects"
    bl_idname = "CAMHELPER_PT_camera_effects"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'CamHelper'
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.cam_helper_props
        
        # Camera Path
        box = layout.box()
        box.label(text="Camera Path")
        
        row = box.row()
        row.prop(props, "path_type")
        
        row = box.row()
        row.prop(props, "path_frames")
        
        row = box.row()
        row.operator("camhelper.create_path")
        
        # Dolly Zoom
        box = layout.box()
        box.label(text="Dolly Zoom")
        
        row = box.row()
        row.prop(props, "use_dolly_zoom")
        
        if props.use_dolly_zoom:
            row = box.row()
            row.prop(props, "dolly_zoom_strength")
            
            row = box.row()
            row.operator("camhelper.dolly_zoom")
        
        # Camera Roll
        box = layout.box()
        box.label(text="Camera Roll")
        
        row = box.row()
        row.prop(props, "enable_roll")
        
        if props.enable_roll:
            row = box.row()
            row.prop(props, "roll_angle")
            
            row = box.row()
            row.operator("camhelper.add_roll")  

class CAMHELPER_OT_bind_cameras(Operator):
    bl_idname = "camhelper.bind_cameras"
    bl_label = "Bind Cameras"
    
    def create_linear_path(self, context, selected_cameras):
        props = context.scene.cam_helper_props
        
        # Sort cameras by name to ensure consistent order
        cameras = sorted(selected_cameras, key=lambda x: x.name)
        
        # Create empty as path parent
        bpy.ops.object.empty_add(type='PLAIN_AXES')
        path_empty = context.active_object
        path_empty.name = "CameraPath"
        
        # Create curve path
        curve_data = bpy.data.curves.new(name="CameraPath", type='CURVE')
        curve_data.dimensions = '3D'
        
        # Create spline
        spline = curve_data.splines.new(type='BEZIER')
        spline.bezier_points.add(len(cameras) - 1)
        
        # Set points from camera positions
        for i, cam in enumerate(cameras):
            point = spline.bezier_points[i]
            point.co = path_empty.matrix_world.inverted() @ cam.location
            point.handle_left_type = 'AUTO'
            point.handle_right_type = 'AUTO'
            
            # Parent camera to path
            cam.parent = path_empty
        
        # Create curve object
        curve_obj = bpy.data.objects.new("CameraPath", curve_data)
        context.collection.objects.link(curve_obj)
        curve_obj.parent = path_empty
        
        return path_empty
    
    def create_circular_path(self, context, selected_cameras):
        props = context.scene.cam_helper_props
        
        # Calculate center point
        center = Vector((0, 0, 0))
        for cam in selected_cameras:
            center += cam.location
        center /= len(selected_cameras)
        
        # Create empty at center
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=center)
        center_empty = context.active_object
        center_empty.name = "CameraCircle"
        
        # Arrange cameras in circle
        radius = props.orbit_radius
        angle_step = 2 * math.pi / len(selected_cameras)
        
        for i, cam in enumerate(selected_cameras):
            angle = angle_step * i
            
            # Calculate new position
            x = center.x + radius * math.cos(angle)
            y = center.y + radius * math.sin(angle)
            z = cam.location.z
            
            cam.location = Vector((x, y, z))
            
            # Point camera to center
            direction = center - cam.location
            rot_quat = direction.to_track_quat('-Z', 'Y')
            cam.rotation_euler = rot_quat.to_euler()
            
            # Parent to center empty
            cam.parent = center_empty
        
        return center_empty
    
    def create_array(self, context, selected_cameras):
        props = context.scene.cam_helper_props
        
        # Create empty as array parent
        bpy.ops.object.empty_add(type='PLAIN_AXES')
        array_empty = context.active_object
        array_empty.name = "CameraArray"
        
        # Get reference camera (first selected)
        if not selected_cameras:
            self.report({'ERROR'}, "No cameras selected")
            return None
            
        ref_cam = selected_cameras[0]
        spacing = props.binding_distance
        
        # Calculate array direction based on reference camera's forward direction
        forward = ref_cam.matrix_world.to_quaternion() @ Vector((0.0, 0.0, -1.0))
        
        # Position cameras in array
        for i, cam in enumerate(selected_cameras):
            # Calculate new position
            offset = forward * (spacing * i)
            cam.location = ref_cam.location + offset
            
            # Match rotation to reference camera
            cam.rotation_euler = ref_cam.rotation_euler
            
            # Parent to array empty
            cam.parent = array_empty
        
        return array_empty

    def create_orbit(self, context, selected_cameras):
        props = context.scene.cam_helper_props
        
        if not selected_cameras:
            self.report({'ERROR'}, "No cameras selected")
            return None
        
        # Create empty as orbit center
        bpy.ops.object.empty_add(type='PLAIN_AXES')
        orbit_empty = context.active_object
        orbit_empty.name = "CameraOrbit"
        
        # Calculate orbit parameters
        radius = props.orbit_radius
        angle_step = 2 * math.pi / len(selected_cameras)
        
        # Position cameras in orbit
        for i, cam in enumerate(selected_cameras):
            angle = angle_step * i
            
            # Calculate position on orbit
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            z = cam.location.z
            
            cam.location = orbit_empty.location + Vector((x, y, z))
            
            # Point camera to center
            cam.rotation_mode = 'QUATERNION'
            direction = orbit_empty.location - cam.location
            cam.rotation_quaternion = direction.to_track_quat('-Z', 'Y')
            
            # Parent to orbit empty
            cam.parent = orbit_empty
        
        return orbit_empty

    def execute(self, context):
        # Get selected cameras
        selected_cameras = [obj for obj in context.selected_objects if obj.type == 'CAMERA']
        
        if len(selected_cameras) < 2:
            self.report({'ERROR'}, "Please select at least two cameras")
            return {'CANCELLED'}
        
        props = context.scene.cam_helper_props
        
        # Create appropriate binding based on type
        if props.binding_type == 'LINEAR':
            result = self.create_linear_path(context, selected_cameras)
        elif props.binding_type == 'CIRCULAR':
            result = self.create_circular_path(context, selected_cameras)
        elif props.binding_type == 'ARRAY':
            result = self.create_array(context, selected_cameras)
        elif props.binding_type == 'ORBIT':
            result = self.create_orbit(context, selected_cameras)
        
        if result is None:
            return {'CANCELLED'}
        
        return {'FINISHED'}

class CAMHELPER_OT_clear_binding(Operator):
    bl_idname = "camhelper.clear_binding"
    bl_label = "Clear Binding"
    
    def execute(self, context):
        selected_cameras = [obj for obj in context.selected_objects if obj.type == 'CAMERA']
        
        if not selected_cameras:
            self.report({'ERROR'}, "No cameras selected")
            return {'CANCELLED'}
        
        try:
            for cam in selected_cameras:
                # Clear parent
                if cam.parent:
                    matrix_world = cam.matrix_world.copy()
                    cam.parent = None
                    cam.matrix_world = matrix_world
                
                # Clear constraints
                cam.constraints.clear()
            
            self.report({'INFO'}, "Cleared camera bindings")
            return {'FINISHED'}
        
        except Exception as e:
            self.report({'ERROR'}, f"Error clearing binding: {str(e)}")
            return {'CANCELLED'}
            
class CAMHELPER_OT_create_camera_path(Operator):
    bl_idname = "camhelper.create_path"
    bl_label = "Create Camera Path"
    
    def execute(self, context):
        selected_cameras = [obj for obj in context.selected_objects if obj.type == 'CAMERA']
        if len(selected_cameras) < 2:
            self.report({'ERROR'}, "Select at least two cameras")
            return {'CANCELLED'}
        
        props = context.scene.cam_helper_props
        
        try:
            # Create curve
            curve_data = bpy.data.curves.new('CameraPath', type='CURVE')
            curve_data.dimensions = '3D'
            
            # Create spline
            spline = curve_data.splines.new(type='BEZIER')
            spline.bezier_points.add(len(selected_cameras) - 1)
            
            # Set points from camera positions
            for i, cam in enumerate(selected_cameras):
                point = spline.bezier_points[i]
                point.co = cam.location
                point.handle_left_type = 'AUTO'
                point.handle_right_type = 'AUTO'
            
            # Create curve object
            curve_obj = bpy.data.objects.new('CameraPath', curve_data)
            context.collection.objects.link(curve_obj)
            
            # Create follow path constraint
            constraint = context.scene.camera.constraints.new(type='FOLLOW_PATH')
            constraint.target = curve_obj
            constraint.use_fixed_location = True
            constraint.forward_axis = 'FORWARD_Y'
            constraint.up_axis = 'UP_Z'
            
            # Animate path
            curve_obj.data.path_duration = props.path_frames
            curve_obj.data.use_path = True
            
            # Add keyframes
            constraint.offset = 0.0
            constraint.keyframe_insert(data_path="offset", frame=context.scene.frame_start)
            constraint.offset = 1.0
            constraint.keyframe_insert(data_path="offset", frame=context.scene.frame_start + props.path_frames)
            
            self.report({'INFO'}, "Camera path created")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Error creating path: {str(e)}")
            return {'CANCELLED'}

class CAMHELPER_OT_dolly_zoom(Operator):
    bl_idname = "camhelper.dolly_zoom"
    bl_label = "Add Dolly Zoom"
    
    def execute(self, context):
        cam = context.scene.camera
        if not cam:
            self.report({'ERROR'}, "No active camera")
            return {'CANCELLED'}
            
        props = context.scene.cam_helper_props
        
        try:
            # Store initial values
            start_frame = context.scene.frame_current
            initial_loc = cam.location.copy()
            initial_lens = cam.data.lens
            
            # Calculate end values
            direction = cam.matrix_world.to_quaternion() @ Vector((0.0, 0.0, -1.0))
            end_loc = initial_loc + direction * props.dolly_zoom_strength
            end_lens = initial_lens * (1.0 / props.dolly_zoom_strength)
            
            # Set keyframes
            cam.location = initial_loc
            cam.data.lens = initial_lens
            cam.keyframe_insert(data_path="location", frame=start_frame)
            cam.data.keyframe_insert(data_path="lens", frame=start_frame)
            
            cam.location = end_loc
            cam.data.lens = end_lens
            cam.keyframe_insert(data_path="location", frame=start_frame + 50)
            cam.data.keyframe_insert(data_path="lens", frame=start_frame + 50)
            
            # Set interpolation
            for fc in cam.animation_data.action.fcurves:
                for kf in fc.keyframe_points:
                    kf.interpolation = 'LINEAR'
            
            self.report({'INFO'}, "Dolly zoom added")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Error adding dolly zoom: {str(e)}")
            return {'CANCELLED'}

class CAMHELPER_OT_add_roll(Operator):
    bl_idname = "camhelper.add_roll"
    bl_label = "Add Camera Roll"
    
    def execute(self, context):
        cam = context.scene.camera
        if not cam:
            self.report({'ERROR'}, "No active camera")
            return {'CANCELLED'}
            
        props = context.scene.cam_helper_props
        
        try:
            # Convert angle to radians
            angle = math.radians(props.roll_angle)
            
            # Set rotation
            current_rot = cam.rotation_euler.copy()
            cam.rotation_euler.rotate_axis('Y', angle)
            
            self.report({'INFO'}, "Camera roll applied")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Error applying roll: {str(e)}")
            return {'CANCELLED'}
			
class CAMHELPER_OT_add_camera(Operator):
    bl_idname = "camhelper.add_camera"
    bl_label = "Add Camera"
    
    def execute(self, context):
        # Create new camera
        bpy.ops.object.camera_add()
        new_cam = context.active_object
        
        # Add to our list
        item = context.scene.camera_list.add()
        item.name = new_cam.name
        item.camera = new_cam
        context.scene.camera_list_index = len(context.scene.camera_list) - 1
        return {'FINISHED'}

class CAMHELPER_OT_remove_camera(Operator):
    bl_idname = "camhelper.remove_camera"
    bl_label = "Remove Camera"
    
    def execute(self, context):
        scene = context.scene
        idx = scene.camera_list_index
        
        if idx >= 0 and len(scene.camera_list) > 0:
            item = scene.camera_list[idx]
            # Remove camera object if it exists
            if item.camera:
                bpy.data.objects.remove(item.camera, do_unlink=True)
            scene.camera_list.remove(idx)
            scene.camera_list_index = min(idx, len(scene.camera_list) - 1)
            
        return {'FINISHED'}
		
			
class CAMHELPER_OT_set_active_camera(Operator):
    bl_idname = "camhelper.set_active_camera"
    bl_label = "Set Active Camera"
    
    def execute(self, context):
        scene = context.scene
        idx = scene.camera_list_index
        
        if idx >= 0 and len(scene.camera_list) > 0:
            item = scene.camera_list[idx]
            if item.camera:
                scene.camera = item.camera
                
        return {'FINISHED'}

		
class CAMHELPER_OT_create_camera_group(Operator):
    bl_idname = "camhelper.create_camera_group"
    bl_label = "Create Camera Group"
    
    def execute(self, context):
        props = context.scene.cam_helper_props
        group_name = props.active_camera_group
        
        # Create empty as group controller
        bpy.ops.object.empty_add(type='PLAIN_AXES')
        group_empty = context.active_object
        group_empty.name = f"CameraGroup_{group_name}"
        
        # Find all selected cameras
        selected_cameras = [obj for obj in context.selected_objects 
                          if obj.type == 'CAMERA']
        
        if not selected_cameras:
            self.report({'WARNING'}, "No cameras selected")
            return {'CANCELLED'}
            
        # Parent cameras to group
        for cam in selected_cameras:
            cam.parent = group_empty
            
        self.report({'INFO'}, f"Created camera group: {group_name}")
        return {'FINISHED'}	
		
class CAMHELPER_OT_add_dof_empty(Operator):
    bl_idname = "camhelper.add_dof_empty"
    bl_label = "Add DOF Empty"
    
    def execute(self, context):
        active_cam = context.scene.camera
        if not active_cam:
            self.report({'ERROR'}, "No active camera")
            return {'CANCELLED'}
            
        bpy.ops.object.empty_add(type='SPHERE')
        empty = context.active_object
        empty.name = f"{active_cam.name}_DOF"
        
        # Position empty
        direction = active_cam.matrix_world.to_quaternion() @ Vector((0.0, 0.0, -1.0))
        empty.location = active_cam.location + direction * active_cam.data.dof.focus_distance
        
        active_cam.data.dof.focus_object = empty
        
        return {'FINISHED'}		
		
class CAMHELPER_OT_apply_settings(Operator):
    bl_idname = "camhelper.apply_settings"
    bl_label = "Apply Settings"
    
    def execute(self, context):
        active_cam = context.scene.camera
        if not active_cam:
            self.report({'ERROR'}, "No active camera")
            return {'CANCELLED'}
            
        props = context.scene.cam_helper_props
        
        try:
            # Apply DOF settings
            if active_cam.data.dof.use_dof:
                active_cam.data.dof.focus_distance = props.dof_focus_distance
                active_cam.data.dof.aperture_fstop = props.dof_aperture
            
            # Apply passepartout settings - Fixed version
            active_cam.data.show_passepartout = True
            active_cam.data.passepartout_alpha = props.passepartout_alpha  
            
            # Apply safe areas
            active_cam.data.show_safe_areas = props.show_safe_areas
            if props.show_safe_areas:
                safe_areas = active_cam.data.safe_areas
                safe_areas.title[0] = props.safe_area_percentage
                safe_areas.title[1] = props.safe_area_percentage
                safe_areas.action[0] = props.safe_area_percentage
                safe_areas.action[1] = props.safe_area_percentage
            
            # Apply composition guides
            active_cam.data.show_composition_guides = props.show_composition_guides
            if props.show_composition_guides:
                # Reset all composition guide settings first
                active_cam.data.show_composition_thirds = False
                active_cam.data.show_composition_center = False
                active_cam.data.show_composition_golden = False
                active_cam.data.show_composition_golden_tria_a = False
                active_cam.data.show_composition_golden_tria_b = False
                
                # Apply selected guide type
                if props.guide_type == 'THIRDS':
                    active_cam.data.show_composition_thirds = True
                elif props.guide_type == 'CENTER':
                    active_cam.data.show_composition_center = True
                elif props.guide_type == 'GOLDEN':
                    active_cam.data.show_composition_golden = True
                elif props.guide_type == 'GOLDEN_TRI':
                    active_cam.data.show_composition_golden_tria_a = True
                    active_cam.data.show_composition_golden_tria_b = True
            
            # Update the viewport
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()
        
            # Apply new features
            if hasattr(active_cam.data, "bg_color"):
                active_cam.data.bg_color = props.camera_background_color
            
            # Apply camera display size
            active_cam.data.display_size = props.camera_display_size
            
            if props.lock_camera_rotation:
                active_cam.lock_rotation = [True, True, True]
            else:
                active_cam.lock_rotation = [False, False, False]
                
            if props.show_camera_path:
                bpy.ops.object.paths_calculate(start_frame=context.scene.frame_start,
                                            end_frame=context.scene.frame_start + props.camera_path_frames)
            else:
                bpy.ops.object.paths_clear()
            
                self.report({'INFO'}, "Camera settings applied successfully")
                return {'FINISHED'}   
        
        except Exception as e:
            self.report({'ERROR'}, f"Error applying settings: {str(e)}")
            return {'CANCELLED'}

class CAMHELPER_OT_align_to_view(Operator):
    bl_idname = "camhelper.align_to_view"
    bl_label = "Align to View"
    
    def execute(self, context):
        if context.scene.camera:
            bpy.ops.view3d.camera_to_view()
            self.report({'INFO'}, "Camera aligned to current view")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "No active camera")
            return {'CANCELLED'}		
		
class CAMHELPER_OT_lock_to_cursor(Operator):
    bl_idname = "camhelper.lock_to_cursor"
    bl_label = "Lock to Cursor"
    
    def execute(self, context):
        active_cam = context.scene.camera
        if not active_cam:
            self.report({'ERROR'}, "No active camera")
            return {'CANCELLED'}
            
        cursor_loc = context.scene.cursor.location
        
        # Create empty at cursor
        bpy.ops.object.empty_add(location=cursor_loc)
        empty = context.active_object
        empty.name = f"{active_cam.name}_Target"
        
        # Create track to constraint
        constraint = active_cam.constraints.new(type='TRACK_TO')
        constraint.target = empty
        constraint.track_axis = 'TRACK_NEGATIVE_Z'
        constraint.up_axis = 'UP_Y'
        
        self.report({'INFO'}, "Camera locked to cursor position")
        return {'FINISHED'}
		
class CAMHELPER_UL_camera_list(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, "name", text="", emboss=False, icon='CAMERA_DATA')
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon='CAMERA_DATA')

				
def update_camera_list(self, context):
    # Get the camera list property
    camera_list = context.scene.cam_helper_props.camera_list
    # Clear existing items
    camera_list.clear()
    
    # Add all cameras to the list
    for obj in bpy.data.objects:
        if obj.type == 'CAMERA':
            item = camera_list.add()
            item.name = obj.name				
				
class CAMHELPER_OT_smooth_camera_transition(Operator):
    bl_idname = "camhelper.smooth_transition"
    bl_label = "Smooth Camera Transition"
    
    target_camera: StringProperty()
    
    def execute(self, context):
        current_cam = context.scene.camera
        target_cam = bpy.data.objects.get(self.target_camera)
        
        if not current_cam or not target_cam:
            return {'CANCELLED'}
            
        props = context.scene.cam_helper_props
        frame_current = context.scene.frame_current
        
        # Store current transform
        start_loc = current_cam.location.copy()
        start_rot = current_cam.rotation_euler.copy()
        
        # Set keyframes for smooth transition
        current_cam.keyframe_insert(data_path="location", frame=frame_current)
        current_cam.keyframe_insert(data_path="rotation_euler", frame=frame_current)
        
        # Set target transform
        context.scene.frame_current += props.transition_duration
        current_cam.location = target_cam.location
        current_cam.rotation_euler = target_cam.rotation_euler
        
        current_cam.keyframe_insert(data_path="location")
        current_cam.keyframe_insert(data_path="rotation_euler")
        
        # Add smooth interpolation
        for fc in current_cam.animation_data.action.fcurves:
            for kf in fc.keyframe_points:
                kf.interpolation = 'BEZIER'
                kf.handle_left_type = 'AUTO_CLAMPED'
                kf.handle_right_type = 'AUTO_CLAMPED'
        
        self.report({'INFO'}, f"Transitioning to {target_cam.name}")
        return {'FINISHED'}
    
class CAMHELPER_OT_set_transition_duration(Operator):
    bl_idname = "camhelper.set_transition_duration"
    bl_label = "Set Transition Duration"
    bl_description = "Set the camera transition duration in frames"
    
    frames: bpy.props.IntProperty(
        name="Frames",
        description="Number of frames for the transition",
        default=1,
        min=1
    )
    
    def execute(self, context):
        props = context.scene.cam_helper_props
        props.transition_duration = self.frames
        return {'FINISHED'} 
				
# Camera Marker Drawing
def draw_camera_markers():
    context = bpy.context
    props = context.scene.cam_helper_props
    
    if not props.show_camera_names:
        return
        
    # Get all cameras in scene
    cameras = [obj for obj in bpy.data.objects if obj.type == 'CAMERA']
    
    shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
    shader.bind()
    
    for cam in cameras:
        # Draw camera icon
        matrix = cam.matrix_world
        size = props.camera_display_size
        
        # Camera frustum vertices
        verts = [
            matrix @ Vector((-size, -size, -size)),
            matrix @ Vector((size, -size, -size)),
            matrix @ Vector((size, size, -size)),
            matrix @ Vector((-size, size, -size)),
            matrix @ Vector((0, 0, size))
        ]
        
        # Draw lines
        shader.uniform_float("color", (1, 1, 1, 1))
        batch = batch_for_shader(shader, 'LINES', {
            "pos": verts
        })
        batch.draw(shader)
        
        # Draw name
        if props.show_camera_names:
            view3d_utils.location_3d_to_region_2d(
                context.region, 
                context.space_data.region_3d,
                cam.location
            )

class CAMHELPER_OT_refresh_camera_list(Operator):
    bl_idname = "camhelper.refresh_camera_list"
    bl_label = "Refresh Camera List"
    
    def execute(self, context):
        scene = context.scene
        cam_helper_props = scene.cam_helper_props
        
        # Clear existing list
        cam_helper_props.camera_list.clear()
        
        # Add all cameras in the scene
        for obj in bpy.data.objects:
            if obj.type == 'CAMERA':
                item = cam_helper_props.camera_list.add()
                item.name = obj.name
        
        return {'FINISHED'}

class CAMHELPER_OT_select_camera(Operator):
    bl_idname = "camhelper.select_camera"
    bl_label = "Select Camera"
    
    camera_name: StringProperty()
    
    def execute(self, context):
        cam = bpy.data.objects.get(self.camera_name)
        if cam:
            bpy.ops.object.select_all(action='DESELECT')
            cam.select_set(True)
            context.view_layer.objects.active = cam
            context.scene.camera = cam
        return {'FINISHED'}
		
class CAMHELPER_OT_enable_passepartout(Operator):
    bl_idname = "camhelper.enable_passepartout"
    bl_label = "Enable Passepartout"
    
    def execute(self, context):
        if context.scene.camera:
            context.scene.camera.data.show_passepartout = True
            return {'FINISHED'}
        return {'CANCELLED'}		
		
# Camera List Panel
class CAMHELPER_PT_camera_list(Panel):
    bl_label = "Camera List"
    bl_idname = "CAMHELPER_PT_camera_list"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "CamHelper"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # Camera List
        row = layout.row()
        row.template_list("CAMHELPER_UL_camera_list", "", scene, "camera_list", 
                         scene, "camera_list_index")
        
        # Camera List Operators
        col = row.column(align=True)
        col.operator("camhelper.add_camera", icon='ADD', text="")
        col.operator("camhelper.remove_camera", icon='REMOVE', text="")
        
        # Active camera operations
        if len(scene.camera_list) > 0 and scene.camera_list_index >= 0:
            layout.operator("camhelper.set_active_camera", icon='CAMERA_DATA')
            
        # Quick actions for active camera
        col.operator("camhelper.align_to_view", icon='VIEW_CAMERA', text="")
        col.operator("view3d.view_camera", icon='RESTRICT_VIEW_OFF', text="")
        
        # Camera Stats
        box = layout.box()
        row = box.row()
        row.label(text=f"Total Cameras: {len(scene.camera_list)}")
        if context.scene.camera:
            row = box.row()
            row.label(text=f"Active: {context.scene.camera.name}")


# New Panel for Animation Controls
class CAMHELPER_PT_animation_panel(Panel):
    bl_label = "Camera Animation"
    bl_idname = "CAMHELPER_PT_animation_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'CamHelper'
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.cam_helper_props
        
        # Animation Settings
        box = layout.box()
        box.label(text="Animation Settings")
        
        row = box.row()
        row.prop(props, "animation_speed")
        
        row = box.row()
        row.prop(props, "smooth_transition")
        
        if props.smooth_transition:
            # Transition duration property
            row = box.row()
            row.prop(props, "transition_duration")

            box.separator()
        # Preset buttons label
        row = box.row()
        row.label(text="Duration Presets:")
        # First row of preset buttons (1-10 frames)
        row = box.row(align=True)
        for i in range(1, 11):
            op = row.operator("camhelper.set_transition_duration", text=str(i))
            op.frames = i
        
        # Second row of preset buttons (larger intervals)
        presets = [12, 15, 20, 24, 30, 40, 48, 60, 96, 120]
        row = box.row(align=True)
        for frames in presets:
            op = row.operator("camhelper.set_transition_duration", text=str(frames))
            op.frames = frames

        # Camera Shake
        box = layout.box()
        box.label(text="Camera Shake")
        
        row = box.row()
        row.prop(props, "enable_camera_shake")
        
        if props.enable_camera_shake:
            row = box.row(align=True)
            row.prop(props, "shake_strength")
            row.prop(props, "shake_frequency")
            
            row = box.row(align=True)
            row.operator("camhelper.add_shake")
            row.operator("camhelper.clear_camera_shake")

# New Panel for Multi-Camera Management
class CAMHELPER_PT_multicam_panel(Panel):
    bl_label = "Multi-Camera"
    bl_idname = "CAMHELPER_PT_multicam_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'CamHelper'
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.cam_helper_props
        
        # Camera Groups
        box = layout.box()
        box.label(text="Camera Groups")
        
        row = box.row()
        row.prop(props, "active_camera_group")
        row.operator("camhelper.create_camera_group", text="", icon='GROUP')
        
        # Camera List
        box = layout.box()
        box.label(text="Scene Cameras")
        
        for obj in bpy.data.objects:
            if obj.type == 'CAMERA':
                row = box.row(align=True)
                row.label(text=obj.name, icon='CAMERA_DATA')
                row.operator(
                    "camhelper.smooth_transition",
                    text="",
                    icon='VIEW_CAMERA'
                ).target_camera = obj.name

# UI Panels
class CAMHELPER_PT_main_panel(Panel):
    bl_label = "CamHelper"
    bl_idname = "CAMHELPER_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'CamHelper'
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.cam_helper_props
        active_cam = scene.camera
        
        # Camera selection
        layout.label(text="Active Camera:")
        row = layout.row()
        row.prop(scene, "camera", text="")
        row.operator("camhelper.add_camera", text="", icon='ADD')
        
        if active_cam:
            # Quick Actions
            box = layout.box()
            box.label(text="Quick Actions")
            row = box.row(align=True)
            row.operator("camhelper.align_to_view", icon='VIEW_CAMERA')
            row.operator("camhelper.lock_to_cursor", icon='PIVOT_CURSOR')
            # Passepartout settings
            box = layout.box()
            box.label(text="Passepartout Settings")
            
            # Show current camera's passepartout value
            active_obj = context.active_object
            if active_obj and active_obj.type == 'CAMERA':
                row = box.row()
                row.prop(active_obj.data, "passepartout_alpha", slider=True)
            else:
                row = box.row()
                row.prop(props, "passepartout_alpha", slider=True)
                row = box.row()
                row.operator("camhelper.update_passepartout", text="Apply Passepartout")
            
            # Make sure passepartout is enabled
            if not active_cam.data.show_passepartout:
                row = box.row()
                row.label(text="Passepartout is disabled", icon='ERROR')
                row.operator("camhelper.enable_passepartout", text="Enable", icon='CHECKMARK')
            
            # Camera Transform
            box = layout.box()
            box.label(text="Transform")
            col = box.column(align=True)
            col.prop(active_cam, "location")
            col.prop(active_cam, "rotation_euler")
            
            # Camera settings
            box = layout.box()
            box.label(text="Camera Settings")
            row = box.row()
            row.prop(active_cam.data, "lens", text="Focal Length")
            
            # Resolution
            box.label(text="Resolution:")
            row = box.row(align=True)
            row.prop(scene.render, "resolution_x", text="X")
            row.prop(scene.render, "resolution_y", text="Y")
            row.prop(scene.render, "resolution_percentage", text="%")
            
            # FPS
            row = box.row()
            row.prop(scene.render, "fps", text="FPS")
            
            # DOF Settings
            box = layout.box()
            box.label(text="Depth of Field")
            row = box.row()
            row.prop(active_cam.data.dof, "use_dof", text="Enable DOF")
            
            if active_cam.data.dof.use_dof:
                row = box.row()
                row.prop(props, "dof_focus_distance")
                row = box.row()
                row.prop(props, "dof_aperture")
                row = box.row()
                row.operator("camhelper.add_dof_empty")
                       
            
            # Safe Areas
            box = layout.box()
            box.label(text="Safe Areas")
            row = box.row()
            row.prop(props, "show_safe_areas")
            if props.show_safe_areas:
                row = box.row()
                row.prop(props, "safe_area_percentage")
            
            # Composition Guides
            box = layout.box()
            box.label(text="Composition")
            row = box.row()
            row.prop(props, "show_composition_guides")
            if props.show_composition_guides:
                row = box.row()
                row.prop(props, "guide_type")
            
            # Animation
            box = layout.box()
            box.label(text="Animation")
            row = box.row()
            row.prop(props, "show_camera_path")
            if props.show_camera_path:
                row = box.row()
                row.prop(props, "camera_path_frames")
            
            # Camera Lock
            box = layout.box()
            box.label(text="Camera Lock")
            row = box.row()
            row.prop(props, "lock_camera_rotation")
            
           
			
class BEATANALYZER_PT_panel(Panel):
    bl_label = "Beat Analyzer"
    bl_idname = "BEATANALYZER_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'CamHelper'
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.beat_analyzer_props
        
        # File selection
        box = layout.box()
        box.label(text="Audio File", icon='SOUND')
        box.prop(props, "audio_file", text="")
        
        # Analysis settings
        box = layout.box()
        box.label(text="Analysis Settings", icon='SETTINGS')
        box.prop(props, "chunk_size")
        box.prop(props, "threshold")
        
        # Marker settings
        box = layout.box()
        box.label(text="Marker Settings", icon='MARKER')
        box.prop(props, "marker_prefix")
        box.prop(props, "marker_color")
        box.prop(props, "clear_existing")
        
        # Analyze button
        row = layout.row()
        row.scale_y = 2.0
        row.operator("beatanalyzer.analyze_audio", icon='PLAY')

def register():
    # Register property groups first
    bpy.utils.register_class(CameraCollection)
    bpy.utils.register_class(CameraListProperties)
    bpy.utils.register_class(CameraListItem)
    bpy.utils.register_class(CamHelperProperties)
    bpy.utils.register_class(BeatAnalyzerProperties)
    
    # Register UI classes
    bpy.utils.register_class(CAMHELPER_UL_camera_list)
    bpy.utils.register_class(CAMHELPER_PT_camera_list)
    bpy.utils.register_class(CAMHELPER_PT_main_panel)
    bpy.utils.register_class(CAMHELPER_PT_animation_panel)
    bpy.utils.register_class(CAMHELPER_PT_multicam_panel)
    bpy.utils.register_class(CAMHELPER_PT_camera_effects)
    bpy.utils.register_class(BEATANALYZER_PT_panel)
    
    # Register operators
    bpy.utils.register_class(CAMHELPER_OT_set_active_camera)
    bpy.utils.register_class(CAMHELPER_OT_update_passepartout)
    bpy.utils.register_class(CAMHELPER_OT_add_camera)
    bpy.utils.register_class(CAMHELPER_OT_remove_camera)
    bpy.utils.register_class(CAMHELPER_OT_add_dof_empty)
    bpy.utils.register_class(CAMHELPER_OT_apply_settings)
    bpy.utils.register_class(CAMHELPER_OT_align_to_view)
    bpy.utils.register_class(CAMHELPER_OT_lock_to_cursor)
    bpy.utils.register_class(CAMHELPER_OT_add_camera_shake)
    bpy.utils.register_class(CAMHELPER_OT_clear_camera_shake)
    bpy.utils.register_class(CAMHELPER_OT_create_camera_group)
    bpy.utils.register_class(CAMHELPER_OT_smooth_camera_transition)
    bpy.utils.register_class(CAMHELPER_OT_enable_passepartout)
    bpy.utils.register_class(CAMHELPER_OT_create_camera_path)
    bpy.utils.register_class(CAMHELPER_OT_dolly_zoom)
    bpy.utils.register_class(CAMHELPER_OT_add_roll)
    bpy.utils.register_class(CAMHELPER_OT_set_transition_duration)
    bpy.utils.register_class(BEATANALYZER_OT_analyze_audio)
    
    # Register draw handler
    if not bpy.app.background:
        bpy.types.SpaceView3D.draw_handler_add(
            draw_camera_markers, (), 'WINDOW', 'POST_VIEW'
        )
    
    # Register properties
    bpy.types.Scene.cam_helper_props = bpy.props.PointerProperty(type=CamHelperProperties)
    bpy.types.Scene.camera_list_props = bpy.props.PointerProperty(type=CameraListProperties)
    bpy.types.Scene.beat_analyzer_props = bpy.props.PointerProperty(type=BeatAnalyzerProperties)
    bpy.types.Scene.camera_list = bpy.props.CollectionProperty(type=CameraListItem)
    bpy.types.Scene.camera_list_index = IntProperty()
    bpy.types.Scene.camera_presets = {}

def unregister():
    # Remove properties
    del bpy.types.Scene.cam_helper_props
    del bpy.types.Scene.camera_list_props
    del bpy.types.Scene.beat_analyzer_props
    del bpy.types.Scene.camera_list
    del bpy.types.Scene.camera_list_index
    del bpy.types.Scene.camera_presets
    
    # Unregister operators
    bpy.utils.unregister_class(BEATANALYZER_OT_analyze_audio)
    bpy.utils.unregister_class(CAMHELPER_OT_set_transition_duration)
    bpy.utils.unregister_class(CAMHELPER_OT_add_roll)
    bpy.utils.unregister_class(CAMHELPER_OT_dolly_zoom)
    bpy.utils.unregister_class(CAMHELPER_OT_create_camera_path)
    bpy.utils.unregister_class(CAMHELPER_OT_enable_passepartout)
    bpy.utils.unregister_class(CAMHELPER_OT_smooth_camera_transition)
    bpy.utils.unregister_class(CAMHELPER_OT_create_camera_group)
    bpy.utils.unregister_class(CAMHELPER_OT_clear_camera_shake)
    bpy.utils.unregister_class(CAMHELPER_OT_remove_camera)
    bpy.utils.unregister_class(CAMHELPER_OT_add_camera_shake)
    bpy.utils.unregister_class(CAMHELPER_OT_lock_to_cursor)
    bpy.utils.unregister_class(CAMHELPER_OT_align_to_view)
    bpy.utils.unregister_class(CAMHELPER_OT_apply_settings)
    bpy.utils.unregister_class(CAMHELPER_OT_add_dof_empty)
    bpy.utils.unregister_class(CAMHELPER_OT_add_camera)
    bpy.utils.unregister_class(CAMHELPER_OT_update_passepartout)
    bpy.utils.unregister_class(CAMHELPER_OT_set_active_camera)
    
    # Unregister UI classes
    bpy.utils.unregister_class(BEATANALYZER_PT_panel)
    bpy.utils.unregister_class(CAMHELPER_PT_camera_effects)
    bpy.utils.unregister_class(CAMHELPER_PT_multicam_panel)
    bpy.utils.unregister_class(CAMHELPER_PT_animation_panel)
    bpy.utils.unregister_class(CAMHELPER_PT_main_panel)
    bpy.utils.unregister_class(CAMHELPER_PT_camera_list)
    bpy.utils.unregister_class(CAMHELPER_UL_camera_list)
    
    # Unregister property groups last
    bpy.utils.unregister_class(BeatAnalyzerProperties)
    bpy.utils.unregister_class(CamHelperProperties)
    bpy.utils.unregister_class(CameraListProperties)
    bpy.utils.unregister_class(CameraListItem)
    bpy.utils.unregister_class(CameraCollection)

if __name__ == "__main__":
    register()