# Circular Polar Calendar - Web Frontend Implementation Plan

## Overview
This plan outlines the step-by-step implementation of a web-based frontend for the Circular Polar Calendar application using Bottle framework. Each step is designed to be small, iterative, and testable.

## Prerequisites
- Existing circular polar calendar codebase
- Python 3.8+
- Basic understanding of Bottle framework

---

## Phase 1: Foundation Setup (Steps 1-4)

### Step 1: Project Structure Setup
**Goal**: Create basic web project structure
**Estimated Time**: 30 minutes
**Testable**: Verify directory structure exists

**Tasks**:
1. Create `web/` directory in project root
2. Create subdirectories:
   ```
   web/
   ├── static/
   │   ├── css/
   │   ├── js/
   │   └── images/
   ├── templates/
   ├── storage/
   │   ├── configurations/
   │   └── presets/
   ├── api/
   ├── services/
   └── models/
   ```
3. Create empty `__init__.py` files in each Python package directory

**Test**: 
```bash
cd web
find . -type d
# Should show all created directories
```

---

### Step 2: Basic Bottle Application
**Goal**: Create minimal working web server
**Estimated Time**: 45 minutes
**Testable**: Web server responds to requests

**Tasks**:
1. Create `web/app.py`:
   ```python
   from bottle import Bottle, run, template, static_file
   import os
   
   app = Bottle()
   
   @app.route('/')
   def index():
       return template('index.html', title='Calendar Builder')
   
   @app.route('/static/<filename:path>')
   def static(filename):
       return static_file(filename, root='static')
   
   if __name__ == '__main__':
       run(app, host='localhost', port=8080, debug=True)
   ```

2. Create `web/templates/base.html`:
   ```html
   <!DOCTYPE html>
   <html>
   <head>
       <title>{{title}}</title>
       <meta charset="utf-8">
   </head>
   <body>
       {% block content %}{% endblock %}
   </body>
   </html>
   ```

3. Create `web/templates/index.html`:
   ```html
   {% extends "base.html" %}
   {% block content %}
   <h1>Circular Polar Calendar Builder</h1>
   <p>Welcome to the calendar builder!</p>
   {% endblock %}
   ```

**Test**:
```bash
cd web
python app.py
# Visit http://localhost:8080
# Should see "Circular Polar Calendar Builder" page
```

---

### Step 3: Basic Configuration Storage
**Goal**: Implement JSON-based configuration storage
**Estimated Time**: 1 hour
**Testable**: Can save/load configurations

**Tasks**:
1. Create `web/models/config_models.py` (as outlined in previous proposal)
2. Create `web/services/config_storage.py`:
   ```python
   from models.config_models import ConfigStorage
   
   # Initialize storage
   storage = ConfigStorage()
   ```
3. Create `web/api/config_api.py` with basic endpoints:
   - `GET /api/configurations` - List configurations
   - `POST /api/configurations` - Save configuration
   - `GET /api/configurations/<name>` - Get specific configuration

4. Update `web/app.py` to include API routes

**Test**:
```bash
# Test API endpoints
curl http://localhost:8080/api/configurations
# Should return empty list initially

curl -X POST http://localhost:8080/api/configurations -H "Content-Type: application/json" -d '{"name":"test","config_data":{"city_name":"Nagpur"}}'
# Should save and return success
```

---

### Step 4: Basic Calendar Generation Service
**Goal**: Create service to generate calendars from web config
**Estimated Time**: 1.5 hours
**Testable**: Can generate calendar from web request

**Tasks**:
1. Create `web/services/calendar_builder.py`:
   ```python
   import sys
   import os
   sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
   
   from components.config import load_config
   from components.data_handler import DataHandler
   from components.base_calendar_plotter import BaseCalendarPlotter
   from components.layer_dawn import DawnLayer
   from components.layer_temperature import TemperatureLayer
   
   class CalendarBuilder:
       def __init__(self):
           self.available_layers = {
               'dawn': DawnLayer,
               'temperature': TemperatureLayer,
           }
       
       def build_calendar(self, config_data):
           # Parse web config to internal config format
           config = self._parse_web_config(config_data)
           
           # Load data
           data_handler = DataHandler(config)
           config.dawn_data, config.weather_data, config.city_data, config.sun_data = data_handler.load_data()
           
           # Build layers
           layers = [self.available_layers[layer](config) for layer in config_data.get('selected_layers', ['dawn'])]
           
           # Generate calendar
           plotter = BaseCalendarPlotter(config)
           return plotter.create_plot(layers=layers)
   ```

2. Add calendar generation endpoint to `web/api/calendar_api.py`

**Test**:
```bash
curl -X POST http://localhost:8080/api/generate \
  -H "Content-Type: application/json" \
  -d '{"city_name":"Nagpur","selected_layers":["dawn","temperature"]}'
# Should generate calendar and return filename
```

---

## Phase 2: Core UI Development (Steps 5-8)

### Step 5: Basic Layer Selection UI
**Goal**: Create interface for selecting calendar layers
**Estimated Time**: 1 hour
**Testable**: Can select/deselect layers

**Tasks**:
1. Create `web/templates/builder.html`:
   ```html
   {% extends "base.html" %}
   {% block content %}
   <div class="calendar-builder">
       <div class="layers-panel">
           <h3>Select Layers</h3>
           <div class="layer-checkboxes">
               <label><input type="checkbox" value="dawn"> Dawn/Twilight</label>
               <label><input type="checkbox" value="temperature"> Temperature</label>
               <label><input type="checkbox" value="precipitation"> Precipitation</label>
               <label><input type="checkbox" value="holidays"> Holidays</label>
           </div>
       </div>
       
       <div class="config-panel">
           <h3>Configuration</h3>
           <label>City: <select name="city_name">
               <option value="Nagpur">Nagpur</option>
               <option value="Mumbai">Mumbai</option>
               <option value="New York">New York</option>
           </select></label>
           <label>Year: <input type="number" name="year" value="2025"></label>
       </div>
       
       <button id="generate-btn">Generate Calendar</button>
   </div>
   {% endblock %}
   ```

2. Create `web/static/css/style.css` with basic styling
3. Update `web/app.py` to serve builder page

**Test**:
- Visit `http://localhost:8080/builder`
- Verify checkboxes work
- Verify form elements are functional

---

### Step 6: JavaScript Integration
**Goal**: Add interactive functionality to the builder
**Estimated Time**: 1.5 hours
**Testable**: Can submit form and get response

**Tasks**:
1. Create `web/static/js/calendar-builder.js`:
   ```javascript
   document.addEventListener('DOMContentLoaded', function() {
       const generateBtn = document.getElementById('generate-btn');
       const form = document.querySelector('.calendar-builder');
       
       generateBtn.addEventListener('click', function() {
           const formData = new FormData(form);
           const config = {
               city_name: formData.get('city_name'),
               year: parseInt(formData.get('year')),
               selected_layers: Array.from(document.querySelectorAll('input[type="checkbox"]:checked'))
                   .map(cb => cb.value)
           };
           
           fetch('/api/generate', {
               method: 'POST',
               headers: {'Content-Type': 'application/json'},
               body: JSON.stringify(config)
           })
           .then(response => response.json())
           .then(data => {
               if (data.success) {
                   alert('Calendar generated: ' + data.filename);
               } else {
                   alert('Error: ' + data.error);
               }
           });
       });
   });
   ```

2. Include JavaScript in `builder.html`
3. Add error handling and loading states

**Test**:
- Select layers and city
- Click generate button
- Verify API call is made and response is handled

---

### Step 7: Preview Functionality
**Goal**: Add real-time preview of calendar
**Estimated Time**: 2 hours
**Testable**: Can see preview without full generation

**Tasks**:
1. Add preview endpoint to `web/api/calendar_api.py`:
   ```python
   @app.route('/api/preview', method='POST')
   def preview_calendar():
       config_data = request.json
       config_data['preview'] = True  # Generate smaller version
       builder = CalendarBuilder()
       result = builder.build_calendar(config_data)
       return {'success': True, 'preview_url': result['preview_url']}
   ```

2. Modify `CalendarBuilder` to support preview mode
3. Add preview area to `builder.html`:
   ```html
   <div class="preview-area">
       <h3>Preview</h3>
       <img id="preview-image" src="" alt="Calendar Preview" style="max-width: 400px;">
   </div>
   ```

4. Update JavaScript to call preview on form changes

**Test**:
- Change form settings
- Verify preview updates automatically
- Verify preview is smaller/faster than full generation

---

### Step 8: Output Format Selection
**Goal**: Add basic output format options
**Estimated Time**: 1.5 hours
**Testable**: Can select different output formats

**Tasks**:
1. Add output format section to `builder.html`:
   ```html
   <div class="output-panel">
       <h3>Output Format</h3>
       <label><input type="radio" name="format_type" value="calendar" checked> Regular Calendar</label>
       <label><input type="radio" name="format_type" value="wallpaper"> Wallpaper</label>
       
       <div id="wallpaper-settings" style="display:none">
           <label>Resolution: 
               <select name="wallpaper_resolution">
                   <option value="hd">HD (1920x1080)</option>
                   <option value="4k">4K (3840x2160)</option>
               </select>
           </label>
       </div>
   </div>
   ```

2. Add JavaScript to show/hide format-specific settings
3. Update `CalendarBuilder` to handle different output formats

**Test**:
- Switch between calendar and wallpaper formats
- Verify wallpaper settings appear/disappear
- Generate both formats and verify differences

---

## Phase 3: Advanced Features (Steps 9-12)

### Step 9: Configuration Management UI
**Goal**: Add save/load configuration functionality
**Estimated Time**: 2 hours
**Testable**: Can save and load configurations

**Tasks**:
1. Add configuration management section to `builder.html`
2. Create JavaScript functions for save/load operations
3. Add configuration list/gallery
4. Implement configuration validation

**Test**:
- Save current configuration with a name
- Load saved configuration
- Verify form is populated correctly

---

### Step 10: Color Theme Selection
**Goal**: Add color theme picker
**Estimated Time**: 1.5 hours
**Testable**: Can select different color themes

**Tasks**:
1. Create `web/services/config_presets.py` with theme definitions
2. Add theme selection to UI
3. Update `CalendarBuilder` to apply themes
4. Add theme preview functionality

**Test**:
- Select different themes
- Generate calendar with different themes
- Verify colors change appropriately

---

### Step 11: Advanced Layer Configuration
**Goal**: Add layer-specific settings
**Estimated Time**: 2.5 hours
**Testable**: Can configure individual layer settings

**Tasks**:
1. Add collapsible sections for each layer's settings
2. Implement layer-specific configuration options:
   - Temperature offset settings
   - Strava target settings
   - Holiday layer options
3. Add real-time preview updates for layer changes

**Test**:
- Configure temperature layer offset
- Set Strava running target
- Verify changes affect preview

---

### Step 12: File Management and Download
**Goal**: Add file management and download capabilities
**Estimated Time**: 1.5 hours
**Testable**: Can download generated calendars

**Tasks**:
1. Add file listing endpoint
2. Create download functionality
3. Add file management UI
4. Implement file cleanup/management

**Test**:
- Generate calendar
- Download generated file
- List all generated files
- Delete files

---

## Phase 4: Polish and Optimization (Steps 13-15)

### Step 13: Error Handling and Validation
**Goal**: Add comprehensive error handling
**Estimated Time**: 1.5 hours
**Testable**: Graceful error handling

**Tasks**:
1. Add input validation
2. Implement error handling for all API endpoints
3. Add user-friendly error messages
4. Add loading states and progress indicators

**Test**:
- Submit invalid data
- Test with missing city data
- Verify error messages are helpful

---

### Step 14: UI/UX Improvements
**Goal**: Polish the user interface
**Estimated Time**: 2 hours
**Testable**: Better user experience

**Tasks**:
1. Improve CSS styling
2. Add responsive design
3. Implement better form layouts
4. Add tooltips and help text

**Test**:
- Test on different screen sizes
- Verify all UI elements are accessible
- Check form usability

---

### Step 15: Performance Optimization
**Goal**: Optimize for better performance
**Estimated Time**: 1 hour
**Testable**: Faster generation and preview

**Tasks**:
1. Implement caching for generated images
2. Optimize preview generation
3. Add compression for large files
4. Implement background processing for heavy operations

**Test**:
- Generate multiple calendars
- Verify caching works
- Test performance with large files

---

## Testing Strategy

### Unit Tests
- Test each service class individually
- Test API endpoints with mock data
- Test configuration parsing

### Integration Tests
- Test full calendar generation pipeline
- Test file save/load operations
- Test different output formats

### Manual Testing
- Test UI interactions
- Test different browser compatibility
- Test with different screen sizes

### Performance Testing
- Test with large configurations
- Test concurrent users
- Test memory usage

---

## Deployment Considerations

### Development
- Use Bottle's built-in server for development
- Enable debug mode
- Use file-based storage

### Production
- Use WSGI server (Gunicorn/Waitress)
- Consider database for configuration storage
- Implement proper logging
- Add security measures

---

## Success Criteria

### Phase 1 Complete
- [ ] Web server runs and responds
- [ ] Basic configuration storage works
- [ ] Can generate simple calendar

### Phase 2 Complete
- [ ] Full UI for layer selection
- [ ] Interactive form submission
- [ ] Preview functionality works
- [ ] Multiple output formats supported

### Phase 3 Complete
- [ ] Save/load configurations
- [ ] Color theme selection
- [ ] Advanced layer configuration
- [ ] File management

### Phase 4 Complete
- [ ] Robust error handling
- [ ] Polished UI/UX
- [ ] Good performance
- [ ] Production ready

---

## Notes

- Each step should be completed and tested before moving to the next
- Keep the existing calendar generation code unchanged during development
- Use the existing codebase as a reference for proper integration
- Document any changes or additions made to the existing code
- Consider creating a separate branch for web frontend development
