# Spatial Analytics: Museum Visitor Movement Analysis

## Short overall description

This repository contains the data-processing scripts, spatial data, figures and tables used for a Spatial Analytics exam project at Aarhus University created by Zosia Radwanska and Alexandra Ciulisova. The project investigates how the spatial layout of the Nancy Museum of Fine Arts shapes visitor movement patterns across three floors.

The analysis focuses on three main questions:

1. To what extent do visitors follow similar spatial trajectories within each floor, and does trajectory similarity differ between floors as measured by Frechet distance and coefficient of variation?
2. Which rooms function as hubs in room transition networks on each floor and to what extent is average room dwell time correlated with room size, spatial connectivity, number of visitors, and number of paintings?
3. How is room-to-room sequence predictability related to the branching structure of each floor, measured through dominant next-room share, transition entropy, and number of possible next rooms?

The project combines trajectory analysis, room-level spatial annotation, transition network analysis, dwell-time comparison and route predictability measures.

## Data

The project uses the **Behavioural and Identity-Related Dataset (BIRD)** introduced by Worm, Marchal, and Castagnos (2025):

- Paper: https://dl.acm.org/doi/full/10.1145/3708319.3733686
- Dataset/project page: https://mbanv2.loria.fr/

BIRD was collected at the Nancy Museum of Fine Arts and contains visitor movement and identity-related information from 51 museum visitors. Participants explored the museum freely while wearing eye-tracking glasses.

For this project, the most relevant parts of the data were:

- normalized visitor trajectories sampled at regular temporal intervals,
- museum floor-plan geometry,
- wall and object coordinates in JSON format,
- artwork metadata per room,
- participant-level descriptive data,
- semantic visit-level information such as visit duration, distance, and number of items seen.

The dataset is used under the **CC BY-NC-SA 4.0** license. Any reuse of the original BIRD dataset should cite the original paper.

## Repo structure

```text
SpatialAnalytics/
│
├── data/
│   ├── geojson_converted_objects/        # Converted floor-plan objects as GeoJSON
│   ├── museum_walls_plans/               # Original museum wall/floor-plan files
│   ├── normalized_trajectories/          # Normalized trajectory CSV files per visitor
│   ├── polygons/                         # Room polygons used for room-level assignment
│   ├── pre_processed_geojson/            # Preprocessed GeoJSON files
│   ├── questionnaires/                   # Questionnaire and demographic data
│   ├── annotating_map.qgz                # QGIS project used for room annotation
│   └── semantic_info_entire_trajectories.csv # Visit-level semantic information used for descriptive statistics
│
├── src/
│   ├── geojson_json_conversion_scripts/
│   │   ├── json_to_geojson_full.py       # Converts museum JSON objects to GeoJSON
│   │   ├── trajectories_to_geojson.py    # Converts trajectory CSV files to GeoJSON
│   │
│   ├── cds_spatial_descriptive_statistics.Rmd # Descriptive statistics of participants and visits
│   ├── cds_spatial_pathway_analysis.Rmd  # Trajectory-level analysis and Frechet distance calculations
│   └── cds_spatial_room_analysis.Rmd     # Room-level analysis, transition networks and route predictability  
│
├── out/
│   ├── figures/                          # Main plots produced by the analysis
│   └── tables/                           # Summary tables and exported results
│
├── README.md
└── .gitignore
```

## Script function overview

The repository contains three main R Markdown analysis scripts and a set of Python conversion scripts.

### `cds_spatial_descriptive_statistics.Rmd`

Produces descriptive summaries of the participants and visit-level data. This includes demographic distributions, visit duration, walking distance and number of artworks seen.

### `cds_spatial_pathway_analysis.Rmd`

Performs trajectory-level analysis. The script loads spatial trajectory data, filters points by room polygons, converts points into participant-level trajectories, calculates pairwise Fréchet distances, compares trajectory variability across floors and produces movement-density and distance-distribution visualisations.

### `cds_spatial_room_analysis.Rmd`

Performs room-level and sequence-level analysis. This includes room assignment, dwell-time calculation, room transition extraction, transition network analysis, route conformity, dominant next-room share, transition entropy and branching structure comparisons across floors.

### `geojson_json_conversion_scripts/`

Contains Python utilities used to convert from JSON to GeoJSON, and trajectory CSV formats. These scripts support the spatial preprocessing pipeline and make it possible to align the trajectory data with the museum geometry.

## Suggested workflow

A typical workflow is:

1. Convert museum JSON and trajectory CSV files to GeoJSON using the scripts in `src/geojson_json_conversion_scripts/`.
2. Annotate or inspect room boundaries in QGIS using `data/annotating_map.qgz`.
3. Export room polygons and place them in `data/polygons/`.
4. Run `cds_spatial_descriptive_statistics.Rmd` to generate participant and visit-level summaries.
5. Run `cds_spatial_pathway_analysis.Rmd` to calculate trajectory similarity and movement-density outputs.
6. Run `cds_spatial_room_analysis.Rmd` to calculate room transitions, dwell time, network measures, route conformity and branching structure.
7. Inspect generated figures and tables in `out/`.

## Main outputs

The repository exports figures and tables to the `out/` folder. These include:

- Fréchet distance distributions,
- movement density plots,
- room transition network visualisations,
- room conformity plots,
- branching structure plots,
- coefficient of variation summaries,
- descriptive statistics tables,
- dwell-time correlation tables,
- floor-level route exploration summaries.


## Output summary

The project found that visitor movement patterns differed between museum floors. 
- For trajectory similarity, Floor 2 showed smaller raw Fréchet distances and more similar trajectories than Floors 0 and 1. This likely reflects the more constrained and linear layout of Floor 2. However, coefficient of variation comparisons were not statistically significant, suggesting that raw Fréchet distance differences were also influenced by floor size and spatial scale. 
- For room-level dwell time, the time visitors spent in rooms was more strongly associated with room size and number of artworks than with visitor count or approximate network centrality measures. This suggests that dwell time was shaped more by spatial scale and exhibition content than by simple connectivity alone.
- For room transition networks, staircases, entrances and exits played an important role in structuring visitor flow. Some highly connected rooms may therefore function as transition spaces rather than as rooms that are necessarily more attractive or engaging.
- For route predictability, Floor 2 showed the strongest conformity, with dominant room-to-room transitions and low transition entropy. Floors 0 and 1 showed more branching and greater variation in route choice. This suggests that sequence predictability was closely tied to the branching structure of the layout.
Overall, the findings suggest that more constrained layouts produced more predictable visitor movement, while more open layouts allowed greater variation in exploration.


## Steps for improvement

Future versions of the project could improve the analysis by:

- applying the workflow to multiple museums to test whether the findings transfer across different layouts,
- balancing floor-level comparisons by using only visitors who reached all three floors,
- distinguishing exhibition rooms from functional transition spaces such as staircases,
- separating stationary viewing time from walking time,
- including artwork size, period, artist or popularity as additional predictors,
- adding formal space syntax metrics such as visibility, integration and choice,
- validating manually annotated room polygons against a more systematic spatial reference,


## Authors

Project created by **Zosia Radwanska** and **Alexandra Ciulisova** for the Spatial Analytics course at Aarhus University.
