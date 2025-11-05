# Tankers Tracker

## Overview
The Tankers Tracker is a Python application designed to track tanker vessels in real-time using AIS (Automatic Identification System) data. The application visualizes tanker positions on a map and provides information about their routes and destinations.

## Features
- Real-time tracking of tanker vessels.
- Visualization of tanker positions on an interactive map.
- Support for multiple geographical regions.
- Automatic updates of tanker positions and map refresh.

## Project Structure
```
tankers-tracker
├── src
│   ├── tankers_tracker.py       # Main application logic for tracking tankers.
│   ├── config.py                # Configuration settings for the application.
│   └── utils
│       ├── map_generator.py      # Functions for creating and updating the map.
│       └── ais_client.py         # Manages connection to the AIS stream.
├── data
│   └── regions.json             # JSON data defining geographical regions for tracking.
├── static
│   └── styles.css               # CSS styles for the web interface.
├── tests
│   └── test_tracker.py          # Unit tests for the application.
├── .gitignore                   # Specifies files to be ignored by Git.
├── requirements.txt             # Lists dependencies required for the project.
├── README.md                    # Documentation for the project.
└── LICENSE                      # Licensing information for the project.
```

## Installation
1. Clone the repository:
   ```
   git clone <repository-url>
   cd tankers-tracker
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage
1. Run the main application:
   ```
   python src/tankers_tracker.py
   ```

2. Open the generated map in your web browser to view the tanker positions.

## Contributing
Contributions are welcome! Please fork the repository and submit a pull request for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.