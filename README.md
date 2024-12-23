# DP Cam Helper

## Description
DP Cam Helper is a powerful Blender addon that provides comprehensive camera management tools for the viewport. Designed for both cinematographers and 3D artists, it streamlines camera control and enhances visualization capabilities in Blender with professional-grade features for scene composition and camera animation.

## Features

### Camera Management
- Comprehensive camera list management
- Multiple camera selection and batch operations
- Quick camera switching and organization

### Composition Tools
- Dynamic Passepartout controls with real-time opacity adjustment
- Professional composition guides:
  - Rule of Thirds grid
  - Golden Ratio overlay
  - Center markers
  - Diagonal guides
  - Golden Triangle composition
- Customizable safe areas with adjustable margins
- Advanced DOF (Depth of Field) controls:
  - Precise focus distance adjustment
  - F-Stop control (range: 0.95 to 128.0)

### Camera Binding System
Multiple binding modes for complex camera setups:
- **Linear**: Creates straight paths between camera points
- **Circular**: Generates circular paths around a target
- **Array**: Produces systematic camera arrays
- **Orbit**: Creates orbital camera arrangements
  
Binding options include:
- Adjustable binding distance
- Customizable array count (2-10 cameras)
- Variable orbit radius
- Flexible positioning controls

### Animation Features
- Variable animation speed control
- Smooth transition system:
  - Customizable transition duration (1-250 frames)
  - Enable/disable smoothing
  - Intelligent interpolation
- Camera path visualization:
  - Adjustable path display
  - Custom frame range visualization
- Optional camera shake effects for dynamic shots

## Requirements
- Blender 3.0.0 or higher
- Operating System: Windows, macOS, or Linux
- Graphics: OpenGL 2.1 compatible hardware

## Installation
1. Download the DP Cam Helper Pro addon file (.zip)
2. Open Blender and navigate to Edit > Preferences
3. Select the "Add-ons" tab
4. Click "Install" and locate the downloaded .zip file
5. Enable the addon by checking the checkbox next to "3D View: DP Cam Helper"
6. Save preferences (optional but recommended)

## Location
Access the addon through:
- View3D > Sidebar (N-panel) > Cam Helper

## Detailed Usage Guide

### Basic Setup
1. Select or create a camera in your scene
2. Open the Cam Helper panel in the sidebar
3. Adjust basic camera settings through the interface

### Working with Composition
1. Enable composition guides through the panel
2. Select your preferred guide type
3. Adjust safe areas if needed
4. Fine-tune passepartout opacity for better visualization

### Camera Animation
1. Set up multiple cameras in your scene
2. Choose your preferred binding type
3. Adjust binding parameters (distance, count, radius)
4. Enable smooth transitions if desired
5. Set animation speed and transition duration
6. Create keyframes or use auto-animation features

### Advanced Features
- **Camera Lock**: Prevent accidental camera rotation
- **Path Visualization**: Enable camera path display for better planning
- **Shake Effects**: Add procedural camera shake for dynamic shots

### Beat Analyzer System
- Audio-driven camera animation system
- Automatic beat detection and marker creation
- Customizable analysis settings:
  - Adjustable chunk size for analysis precision
  - Configurable threshold for beat detection
  - Custom marker prefix naming
  - Color-coded beat markers
  
#### Beat Analyzer Features
- **Audio File Support**: 
  - Compatible with most common audio formats
  - Direct file selection through Blender's file browser
  
- **Analysis Controls**:
  - Adjustable sensitivity settings
  - Real-time beat detection
  - Customizable analysis parameters
  
- **Marker System**:
  - Automatic marker placement at beat points
  - Color-coded markers for better visualization
  - Option to clear existing markers
  - Custom prefix naming for organized timeline
  
- **Integration**:
  - Seamless integration with camera animation
  - Beat-synchronized camera movements
  - Compatible with other camera animation features

### Working with Beat Analyzer
1. **Setup**:
   - Load your audio file through the Beat Analyzer panel
   - Adjust chunk size and threshold settings
   - Configure marker preferences

2. **Analysis**:
   - Click the "Analyze Audio" button
   - Wait for the analysis to complete
   - Review generated markers in the timeline

3. **Fine-tuning**:
   - Adjust threshold for more/fewer beat markers
   - Modify chunk size for analysis precision
   - Update marker colors and prefixes as needed

4. **Camera Animation**:
   - Use generated markers as keyframe points
   - Synchronize camera movements with beats
   - Combine with other camera effects

[Rest of the README remains the same...]

## Requirements
[Previous requirements plus:]
- Sufficient memory for audio analysis
- Supported audio formats: WAV, MP3, OGG (format support depends on Blender's audio system)

## Troubleshooting
[Previous troubleshooting plus:]
4. **Beat Detection Issues**:
   - Verify audio file format compatibility
   - Adjust threshold and chunk size
   - Check system memory availability
5. **Marker Generation Problems**:
   - Ensure timeline is clear if using "clear existing" option
   - Verify audio file is properly loaded
   - Check marker naming conflicts

## Troubleshooting
Common issues and solutions:
1. **Addon not appearing**: Verify installation and Blender version compatibility
2. **Camera binding issues**: Check for proper camera selection and binding distance
3. **Animation glitches**: Ensure smooth transition duration is appropriate for your frame rate

## License
This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.

## Author
Dimona Patrick
digital pixels forge

## Version
2.0

## Support and Contribution
- Report issues through the project's issue tracker
- Feature requests and suggestions are welcome
- Contributions should follow the project's coding standards
- For support queries, contact: [dimona.patrick@gmail.com]

## Changelog
### Version 2.0
- Initial public release
- Added comprehensive camera management features
- Implemented advanced binding system
- Introduced animation controls
- Added composition guides and safe areas

## Future Development
Planned features and improvements:
- Additional composition guide types
- Enhanced animation presets
- Virtual camera support
- Multi-viewport camera management

## Acknowledgments
- Blender Foundation for the amazing 3D software

