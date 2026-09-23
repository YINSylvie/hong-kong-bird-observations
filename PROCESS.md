# Process

### Approach

I followed the designer's path, with an animated treatment inspired by moving-current maps. I first inspected the raw CSV rather than beginning with a chart type. The useful dimensions were time, longitude, latitude and maximum surface wind. Two consecutive geographic positions define a movement direction, while wind speed can control both colour and stroke weight. This led to a visual grammar in which position remains position, an arrow remains motion, and orange/thicker marks mean stronger winds.

The script reads the committed file from `data/`, skips the three multilingual title lines, and groups observations using the HKO track code. This matters because the file contains two different unnamed systems; grouping only by the displayed name would incorrectly join them into one long track. Latitude and longitude are divided by 100 because the CSV stores them in units of 0.01 degree. The observations are sorted by UTC time before consecutive points are converted into movement vectors.

### Tools and AI use

I used **OpenAI Codex** to inspect the data, compare possible visual approaches, draft a large part of the Python plotting code, and help write the documentation. I used **Matplotlib** for the plotted tracks and arrows, **Pillow** for the animated WebP, and **uv** to declare and resolve the dependencies from the script header. I ran the program repeatedly, inspected the PNG output, and checked the WebP frame count rather than accepting the first generated result.

### One thing I kept

I kept the suggestion to draw equal-length directional arrows while using colour and line weight for wind speed. This was good because arrow length then has one job: showing direction clearly without allowing fast-moving or widely spaced observations to dominate the composition. Teal-to-orange colour and increasing stroke weight provide two redundant signals for intensity, so the strongest sections remain visible even when many tracks overlap.

### One thing I rejected

I rejected the initial idea of downloading online map tiles every time the plot runs. A detailed basemap looked attractive, but it conflicted with the assignment requirement that the repository work with Wi-Fi off. It also added visual detail that was not part of the message. I replaced it with a restrained longitude–latitude grid. The result is less geographically familiar, but it is reproducible offline and keeps attention on motion and wind intensity.

### Corrections and iterations

The generated draft needed several corrections. The CSV does not begin directly with its header; it has three multilingual description lines that must be skipped. Coordinates are stored as integers in hundredths of a degree, not ordinary decimal degrees. Records labelled `nameless` cannot all be grouped together, so I used the HKO code as the track identity. I also reduced the animation to roughly one frame per eighteen hours to keep the WebP small, while retaining all observations in the accumulated track geometry.

Earlier experiments included a storm-intensity lineage, a ranked tick chart and a radial artwork. They were useful for understanding the dataset, but I did not keep them as the final submission because they either summarised away geographic movement or made the work feel like an abstract poster. The current-style track field has a clearer single message: **where the 2024 cyclones moved, and where along those paths they became strong**.
