# DSCAL_Post_processing

## What is this script?
This is a very niche python script, made by a non-developer using a lot of innefficient chat GPT-code. Still, more user friendly than manual tedious file naming...
It looks at a folder containing calibration certificates genereated by DS-CAL 5. It Identifies if the device is a Sirius or not, and then merges the files (if a Sirius) and
renames the protocols with customer ID and the proper as_found etc. suffixes afterwards. Multiple Sirius calibration with the same suffix are not tested, beware...

## How do I use it?
It should be as simple as cloning the repo and running the file with Python installed. It will ask you to point to a folder containing DS-CAL generated calibration certificates.

