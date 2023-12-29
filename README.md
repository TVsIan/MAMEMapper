# MAMEMapper
WIP readme file for v0.01 (Initial Release) - screenshots etc. will be added.

## What is it?

MAMEMapper is designed to make configuring MAME controls as easy as possible. By selecting a controller that matches what you're using, it can create either a single ctrlr file or multiple cfg files to map the controls with your preferred default setting as well as specific configurations for certain games - ie fighting games with more than 4 buttons.

## Notes & Warnings
***BACK UP YOUR CONFIGS AND CTRLR FILES!*** This will overwrite them. You will be warned when running the generation as well.
The .exe version will throw a false positive on some virus scanners. It's a common issue with pyinstaller, unfortunately. If you're concerned, run it via Python directly instead.
The custom controller function is mostly untested, consider it alpha status. I don't have a panel running in keyboard mode to test with, I will happily accept fixes if needed.
The ini editor could use some expanding, but I'm trying to stick with options that are either buried, require manual editing, or that new users won't think of. I'm open to suggestions.
I've tested this as much as possible on my own, but there are very likely other glitches that I haven't encountered. Use at your own risk, back up as needed, please post any issues you come across and feel free to submit fixes, features, mappings, or controllers that may be missing.

## How to Run It
If you're downloading a prebuilt exe, then just extract it to a folder (keep subfolders intact) and run MAMEMapper.exe.

If you would prefer to run from the source, it requires Python 3 (tested from 3.11), along with pyqt6 and xmltodict. You can create a virtual environment to run it - for Windows, bring up a command line and from the folder MAMEMapper is extracted to, run:

    python -m venv .\venv
    .\venv\Scripts\activate.bat
    pip install pyqt6
    pip install xmltodict

Then when you want to run MAMEMapper, use `.\venv\Scripts\activate.bat` to activate the virtual environment (if you're not already in it) and use `python MAMEMapper.py`

## Options etc.
**Locate MAME:** Select your mame.exe file so that MAMEMapper knows where to put the generated files as well as modifying the ini file if selected.
**Run:** Generate using the currently selected options. Note this will replace any files in the cfg folder in cfg mode, or a previously generated ctrlr file (for that layout, including custom controllers that use the same layout) in ctrlr mode. You will be warned once before generating.
**Exit:** Exit.

**Input Options:**

**Physical Controller:** A controller that matches what you're using. This will be used to set the layout for each mapping as well as the button labels on the Preview tab. The default controllers can be used in most cases, but you may need to load a custom config in the case of arcade panels that don't use the default mapping or fightsticks with non-standard layouts. Default controllers are: *(WIP: Add labeled images with default button order)*
 - **XInput (Xbox Style):** standard XBox 360/One/[Series](https://www.xbox.com/en-US/accessories/controllers/xbox-wireless-controller). If you are using a program like DS4Windows to use your DS4/DualSense/Switch controller as XInput, select this one to get the proper button layout.
 - **DInput (Sony Style):** DualShock/[DualSense](https://www.playstation.com/en-us/accessories/dualsense-wireless-controller/). Sony controllers like to send both a button and axis when the analog triggers are pressed, this will use the button as input. In addition, it maps MAME button 11 to the touchpad click, though none of the game-specific mappings will use it.
 - **DInput (Switch Style, Bluetooth):** Nintendo Classic/[Pro](https://www.nintendo.com/us/store/products/pro-controller/)/Dual Joycon layout. This was generated with a Switch Pro controller connected via Bluetooth, as the USB connection only seems to work properly in Steam with Switch controller support enabled.
 - **6-Button (8BitDo M30 XInput):** Uses the layout for the [8BitDo M30 controller](https://download.8bitdo.com/Manual/Controller/M30/M30_Manual.pdf?20220513) when it is in XInput mode. Assumes a controller will have 6 face buttons + 2 shoulder buttons. Use this as a base if you're mapping other 6-button controllers with a set of shoulder buttons (ie a Saturn controller). The DPad is treated as a left analog stick.
 - **6-Button (Retroarch Genesis/Megadrive):** Uses the [layout](https://docs.libretro.com/library/genesis_plus_gx/#joypad) that Retroarch uses for 6-button Sega pads, assumes there are 6 face buttons and no shoulder buttons.
 - **Modern Fightstick:** 8 buttons, with the 3rd column being R1/R2 and the 4th L1/L2 (as seen [here](https://download.8bitdo.com/Manual/Controller/Xbox/Arcade-Stick-for-Xbox.pdf?20231201)). Assumes the stick will be set to D-Pad mode. Older sticks may need to create a custom version of this, as the L/R button placement varied.
 - **6/4 Button (KB):** An arcade panel with 6 buttons each for P1/2 and 4 buttons for 3/4, using default keyboard inputs. Similar to the panel shown [here](https://99livesarcade.com/store/ols/products/four-player-control-panels-arcade1up-only-32x12x4-approx-sanwa-sticks).
 - **6 Buttons w/Offset 7th (KB):** An arcade panel using a hybrid layout with 6 standard buttons and one offset to the lower left, common for layouts that work for Neo Geo and 6-button fighting games. The layout assumes the offset button is #7, and does add an 8th assumed to be left of it, but nothing requires it. An example is the player 1 & 2 controls on [this](https://www.ultimarc.com/arcade-control-panel/) panel.
 - **I-PAC 4 - All Inputs (KB):** An arcade panel set up for 4 players, 8 buttons each, using the default [I-PAC 4](https://www.ultimarc.com/control-interfaces/i-pacs/i-pac4-board/) keyboard mappings. This should also work for the I-PAC 2, but will map keys as if there were 4 players. The default mappings do include keys that MAME uses for menus etc, it may be a good idea to use the Hotkeys option if using this for more than 2 players. If used as a base for custom mapping, unused players will be ignored.
 - **Future?:** Possible additions for controllers with unique layouts and other features.
   - The Hori Fighting Commander Octa for PC will likely be added as a new base configuration at the end of January when it releases, as having 6 face buttons, a D-Pad, and two analog sticks is fairly unique  and well suited for emulators. This could also be used as a base for Retro-Bit's Saturn analog controller, which has the same specs.
   - Older fightsticks may be worth adding, though most of them could be done with a custom controller mapped to the Retroarch 6-button layout or the Modern Fightstick layout.
   - Other arcade panel layouts that may need supported mappings, ie. a panel with an extra Tron stick.
   - Dedicated analog control mapping - ie. set device order, and set specific devices to trackball, dial, lightgun, paddle, etc. per player.

**Load...:** Loads a MAME cfg file to create a custom mapping. Select the cfg file, then the controller that most matches the physical layout. For joystick controls, it will only take the player 1 controls. For keyboard controls, it will read up to 4 players. Make sure the buttons are mapped in MAME in the same order they are in the source controller.

**Delete:** Deletes a custom configuration file, will not delete any of the default files.
 
**Controllers to Map:** Check off the players you want to set controls for. If you are setting up a 2 player arcade cabinet, it's a good idea to uncheck 3 & 4. If Player 1 is unchecked, hotkeys will not be mapped even if selected.
**Layout Preference:** A set of options that affects the default layout.
 - **NES/SNES:**  Moves the buttons on gamepads with 4 face buttons. Using XBox letters - NES is A = 1, B = 2, X = 3, Y = 4. SNES is X = 1, A = 2, B = 3, Y = 4.
 - **Move Primary Button:** If a game has more than one button, and button #1 is named "Jump" or "A" (Playchoice/Vs System), it will flip the button mappings for buttons 1 & 2 for that game. For most games, Jump is on button 2, so this will make the few outliers (TMNT is a notable one) have consistent controls.
 - **Single Button on 1 & 2:** If a game has only one button, its function is duplicated on controller buttons 1 & 2.
 
 **Advanced Options:**
 
 **Mapping Types:** These are the different options that can be applied. Defaults will apply to any game not listed in the specific mappings. All other mappings apply to a specific subset of games, based on the series or control type.
 
 - **Defaults:** Sets default options. If turned off, only the games in the other mappings will apply, everything else will be ignored. In this case, most of the Layout Preference options will be ignored.
 - **Killer Instinct:** 6/8 button controls will match the arcade, 4-button gamepads will match the SNES layout (weak attacks on shoulder buttons).
 - **Mortal Kombat:** 4-button gamepads will match the SNES version. 6-button controls will match the Genesis version. Offset will use the offset button as Run, the top center button as Block.
 - **Neo Geo:** 4-button gamepads will match the Neo Geo Mini. 6-button controls will have A in the lower left, B, C, D on the top row. The offset layout will use the offset button for A and B, C, D on the bottom row. 8-button layouts will use the bottom row.
 - **Q*Bert:** Will map sticks/D-Pads to activate on the diagonals vs. a single direction, to simulate the 45-degree angled 4-way stick on an 8-way input.
 - **Street Fighter:** 6/8 button controls will match the arcade, 4-button gamepads will match the SNES layout (strong attacks on shoulder buttons). This applies to all Capcom 6-button games.
 - **Tekken:** Maps the buttons for the Tekken series to have punches on top, kicks on the bottom.
 - **Twinstick w/Buttons:** Intended for controllers with two sticks, this will map buttons to the shoulder & click buttons. This is meant for games like Battlezone that had one or more buttons on the sticks themsevles, and is designed to fit Virtual On (which is not currently playable). It can work with other layouts, but is not needed for arcade panels that have a second stick.

**Left Stick:** These are options on how to map the single stick for most games and the left stick for twinstick games. The two aren't quite interchangeable, but 3 out of 4 options will affect both sticks.

 - **DPad & Left Stick:** Either control will activate the direction.
 - **DPad Only:** The analog stick will not be used, only the
   DPad.
   **Left Analog Only:** Only the stick will be used, the DPad will
   be ignored (MAME default).
   **P3 Stick (For 3/1/2/4 Panel):** The
   single stick will be mapped normally, the left stick for twinstick
   games will be mapped to Player 3's joystick. If you have an arcade
   panel set up in player 3 - 1 - 2 - 4 order, this will let player 1
   use the left half of the panel for twinstick games as well as mapping
   P2's right stick to P4's stick so they can use the right half.
   
 **Right Stick:** These are options on how to map the right stick for twinstick games.
 - **Face Buttons + Right Stick:** Either control will activate the direction.
 - **Face Buttons Only:** The face buttons be mapped as the stick, useful for controllers with no right stick (ie a SNES controller).
 - **Right Analog Only:** Only the stick will be used, the face buttons will not be mapped.
 - **P2 Controls:** P1's right stick will me mapped to P2's stick. Intended for 2-player control panels.

**Parent ROMs Only:** Will only create configurations for parent ROMs, not clones. In most cases this is fine and the result will be cleaner, there may be some games where the clones have a different number of players or other changes that could affect their mappings.
**Create Default Configs:** If turned on, configs will be created for games that have no special mappings, they only use the default configuration. Generally not needed.
**Map Hotkeys (Coin + Button):** This will map hotkeys to use the Coin button plus another control to activate certain functions (modeled after Retropie/Batocera/Etc.). Note that buttons are based on their position on the controller itself, not other mappings that may apply. Examples will use the XBox names:

 - Back + Menu: Exit
 - Back + A: Menu
 - Back + B: Reset
 - Back + X: Save State
 - Back + Y: Load State
 - Back + LB: Screenshot
 - Back + RB: Toggle UI (disables all other hotkeys until toggled back on, allows the emulated system full keyboard access)
 - Back + LT: Toggle shaders
 - Back + RT: System service button
 - Back + DPad Right: Fast Forward
 - Back + DPad Up: Pause
 - Back + DPad Left: Rewind 1 frame when paused (if rewind is enabled)

 **Move 3/1/2/4 for 3P/4P games:** If using a P3 - P1 - P2 - P4 control panel, this will swap controls for any game with 3 or 4 players to be in P1 - P2 - P3 - P4 order.
 **Use Neo Geo for 4-Button:** If Neo Geo is selected, this will apply the layout to any 4-button game that's not using an existing mapping (ie Tekken). Intended for 6 button or offset button control panels.
 **Map Mouse & Gun Buttons:** If selected, it will add Mouse and Gun button inputs to each button. In most cases, this should prevent lightgun or trackball games from needing to be remapped if using a mouse or gun. If you are exclusively using a keyboard or joystick controller, it is best to leave this unchecked.
 **Map Digital to Analog inputs:** By default, MAME will map the analog stick and mouse to various analog inputs (dial, trackball, lightgun, etc). This will also map the DPad to the "Increment/Decrement" option for each control. So for example, a trackball game could be controlled using a controller with no stick. The speed will be fixed on the movement as opposed to an analog control, so it's not ideal in most cases.
 **Make ctrlr file instead of cfgs:** Instead of creating separate cfg files for each game, this will create a single ctrlr file in the ctrlr folder. This can reduce file clutter as well as making it easier to swap controllers. It will also allow you to remap controls for specific games inside MAME without being overwritten if you run MAMEMapper again.
 **Add ctrlr to mame.ini:** Will add the created ctrlr file to the existing mame.ini so it loads automatically.
 **Use Fixed Device Order:** Allows you to use the Fixed Order tab to map Joystick, Lightgun, and Mouse controls in a specific order. Good to keep specific inputs on arcade cabinets etc.
 
 **Preview:** Lets you see what the controls for specific games will look like with the current options. You can search by title or romset name, or just click a game on the list.

**Fixed Order:** This lets you select the devices to map in order. Note that while MAME does enumerate keyboard devices, it does not support individual keyboards, so those devices are hidden. In addition, Windows will autopopulate 4 XInput joysticks.
**Get List:** Loads MAME (must be closed afterwards) to get the list of available devices. Only needs to be run once unless you change out devices.
🕹️: Adds the currently selected joystick device to the list.
🔫: Adds the currently selected lightgun device to the list.
🖱️: Adds the currently selected mouse device to the list.
❌: Removes the current device from the mappings list.
Clear All: Removes all devices from the mappings list.

**ini Options:** This tab has some options that will allow you to edit mame.ini easily, separate from the mappings.

**Graphics:**

 - **Video Mode:** Select the graphics system MAME will use.
 - **BGFX Rendering:** if bgfx is selected as the video mode, select which backend it will use.
 - **Screen Chains (CRT):** Select the bgfx filtering to use for games with a CRT display (most games).
 - **Screen Chains (LCD):** Select the bgfx filtering to use for games with an LCD display (mostly handhelds or devices)
 - **Screen Chains (SVG):** Select the bgfx filtering to games that use vector images as a display (segmented LCDs like Game & Watch games).
 - **Full Screen:** Launch in full screen vs. Windowed mode.
 - **Triple Buffering:** May help with screen tearing due to sync issues.
 - **Mixed Screens:** Creates separate ini files for games with mixed display types - ie Silent Scope using a CRT for the main game and an LCD for the scope. This will use your CRT chains for the CRT and LCD chains for the LCD.

 **Artwork:**
 

 - **Crop to Screen:** This will set the game's display to the maximum size, then use the artwork only in the blank areas plus overlays/backdrops. If turned off, the game will scale to fit the artwork, possibly resulting in a smaller screen area.

**State:**

 - **Autosave:** Will create a save state when a machine is closed, and autoload it when starting it again. May not work for all machines.
 - **Rewind:** Enable the ability to step backwards one frame at a time when paused.
 - **Rewind Capacity:** Choose how much space to devote to rewind save states, older states will be overwritten when space runs out.

## Command Line
-v --verbose: Will output the debug log to the console while running (only when running via python MAMEMapper.py -v, the standalone exe has no console window). Whether this option is used or not, MAMEMapper.log will be created/re-created for each run.

## Data File Tools
The tools.py file is used to build the gamelist.json that contains all the game information including player count, control types, control labels, and the mappings that apply to each game. In most cases, you won't need to touch this, but if you are trying to create a new mapping file, this would be how to add it in.
The required files to create gamelist.json:
 - **A MAME xml file.** The one used by default is generated by the Arcade64 fork, which leaves out consoles and other non-arcade machines. This prevents custom configs for those from being overwritten.
 - **controls.json.** Can be downloaded from [here](https://github.com/yo1dog/controls-dat-json), or a tool can be used to convert controls.dat to json yourself. The original controls.dat file has not been updated in a while, so many games will be missing control labels in the preview.
 - **csv files for each mapping.** You should have a .json in the /mappings folder, and a .csv in the /datasources folder with matching filenames - ie sf.json and sf.csv. The csv file should be a "Detailed (csv)" export from the [Arcade Database](http://adb.arcadeitalia.net/lista_mame.php). This can be pieced together from multiple exports, just make sure it includes all the games the mapping should apply to, and only those games.
 - **Additional csv files (Optional):** If there are any machines missing from the xml, they can be added by importing them from a csv, in the same format as the mapping csvs. Any games not in the xml that are in the mapping csvs will be automatically added during the import process.

To create the file, run python tools.py. From there:
1. **Load mame.xml File:** Select the file in mame.xml format to import.
2. **Add Games & Clones from CSV:** Only if you have an additional game CSV file.
3. **Add Controls from JSON:** Imports the controls.json file from /datasources
4. **Add Mappings to Game List:** Scans the /mappings folder for jsons, and /datasources for matching csvs.
5. **Merge Data Files:** Combines the temporary /data/controldb.json and /data/gamedb.json into the gamedata.json file.

**Mapping File Format:**
The mapping files are all json-formatted data, containing button swaps for any control layouts that it applies to. One example is:

    {
    	"longname":"Street Fighter",
    	"shortname":"sf",
    	"x360": {
    		"BUTTON1":"BUTTON3",
    		"BUTTON2":"BUTTON4",
    		"BUTTON3":"BUTTON5",
    		"BUTTON4":"BUTTON1",
    		"BUTTON5":"BUTTON2"
    	},
    	"sony": {
    		"BUTTON1":"BUTTON3",
    		"BUTTON2":"BUTTON4",
    		"BUTTON3":"BUTTON5",
    		"BUTTON4":"BUTTON1",
    		"BUTTON5":"BUTTON2"
    	},
    	"switch": {
    		"BUTTON1":"BUTTON3",
    		"BUTTON2":"BUTTON4",
    		"BUTTON3":"BUTTON5",
    		"BUTTON4":"BUTTON1",
    		"BUTTON5":"BUTTON2"
    	},
    	"stick": {
    		"BUTTON1":"BUTTON5",
    		"BUTTON2":"BUTTON6",
    		"BUTTON3":"BUTTON7",
    		"BUTTON4":"BUTTON1",
    		"BUTTON5":"BUTTON2",
    		"BUTTON6":"BUTTON3"
    	},
    	"ipac4": {
    		"BUTTON1":"BUTTON5",
    		"BUTTON2":"BUTTON6",
    		"BUTTON3":"BUTTON7",
    		"BUTTON4":"BUTTON1",
    		"BUTTON5":"BUTTON2",
    		"BUTTON6":"BUTTON3"
    	},
    	"arcade6": {
    		"BUTTON1":"BUTTON4",
    		"BUTTON2":"BUTTON5",
    		"BUTTON3":"BUTTON6",
    		"BUTTON4":"BUTTON1",
    		"BUTTON5":"BUTTON2",
    		"BUTTON6":"BUTTON3"
    	},
    	"offset": {
    		"BUTTON1":"BUTTON4",
    		"BUTTON2":"BUTTON5",
    		"BUTTON3":"BUTTON6",
    		"BUTTON4":"BUTTON1",
    		"BUTTON5":"BUTTON2",
    		"BUTTON6":"BUTTON3"
    	},
    	"m30": {
    		"BUTTON1":"BUTTON4",
    		"BUTTON2":"BUTTON5",
    		"BUTTON3":"BUTTON6",
    		"BUTTON4":"BUTTON1",
    		"BUTTON5":"BUTTON2",
    		"BUTTON6":"BUTTON3"
    	},
    	"retro6": {
    		"BUTTON1":"BUTTON4",
    		"BUTTON2":"BUTTON5",
    		"BUTTON3":"BUTTON6",
    		"BUTTON4":"BUTTON1",
    		"BUTTON5":"BUTTON2",
    		"BUTTON6":"BUTTON3"
    	}
    }

Each block is for a specific controller layout using it's short name (the filename, for default layouts, the one it was based on for custom controllers). Each pair of buttons is a swap for one of MAME's mappings - so for example `"BUTTON1":"BUTTON4"` would move MAME's Button 1 to the controller's Button 4 (as defined in the controller file). Each swap is processed independently, so order does not matter.
It's also possible to define a mapping that only applies in SNES or NES mode. This is currently only used to apply the SNES layout to gamepad-like controllers when there is no other mapping used, but could be used for any mapping. The format would be:

    "x360-SNES": {
    		"BUTTON1":"BUTTON3",
    		"BUTTON2":"BUTTON1",
    		"BUTTON3":"BUTTON2"
    	}
Replace the SNES with NES to apply to that instead.

> Written with [StackEdit](https://stackedit.io/).

