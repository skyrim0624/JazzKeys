import time
import fluidsynth

# Initialize fluidsynth
fs = fluidsynth.Synth()
fs.start(driver="coreaudio")

# Load Apple DLS
sfid = fs.sfload("/System/Library/Components/CoreAudio.component/Contents/Resources/gs_instruments.dls")

# Play grand piano note
fs.program_select(0, sfid, 0, 0)
fs.noteon(0, 60, 100)
time.sleep(1)
fs.noteoff(0, 60)
fs.delete()
