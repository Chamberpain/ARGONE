function notification(message, css_class) {
    $elm = $("#notification");
    $elm.attr('class','').addClass(css_class);
    $elm = $("#notification_text");
    $elm.attr('class','').addClass(css_class);
    $elm.text(message);
    $elm = $("#notification_likesbar");
    $elm.attr('class','').addClass(css_class);
}

// Takes all the options of a regular google map.
function AdriftMap(element, options) {
    if (!options) options = {};

    // Object functions:
    this.center_changed = $.proxy(this._center_changed, this);
    this.run = $.proxy(this._run, this);
    this.url_params = $.proxy(this._url_params, this);
    this.update_history = $.proxy(this._update_history, this);
    this.draw_heat_map_data = $.proxy(this._draw_heat_map_data, this);

    // Set some defaults:
    this.options = {
        zoom: 2,
        maxZoom: 2,
        draggable: true,
        zoomControl: false,
        panControl: true,
        panControlOptions: {
            position: google.maps.ControlPosition.LEFT_BOTTOM
        },
        scrollwheel: false,
        disableDoubleClickZoom: true,
        disableDefaultUI: true,
        center: new google.maps.LatLng(30, 8),
        mapTypeId: google.maps.MapTypeId.ROADMAP,
        styles: [
                {
                    "featureType": "administrative",
                    "stylers": [
                        { "visibility": "off" }
                    ]
                },{
                    "featureType": "landscape",
                    "stylers": [
                        { "color": "#ffffff" }
                    ]
                },{
                    "featureType": "water",
                    "stylers": [
                        { "color": "#309CC0" }
                    ]
                }
            ],

        // non google map options:
        icon: "/static/MarkerDuckie.png",
        historyPageName: '/map',
        jsonEndpoint: '/run',
        radius: 10,
        monthsPerFrame: 2,
    };

    // Merge defaults and user options
    for (var attrname in options) { this.options[attrname] = options[attrname]; }

    //////////// Constructor ////////////

    // Create the map object.
    this.map = new google.maps.Map(element, this.options);

    // Create the heat map objects.
    this.heatMapData = [];
    this.heatmap = new google.maps.visualization.HeatmapLayer({
        data: this.heatMapData,
        radius: 1
    });
    this.marker = new google.maps.Marker({
        map: this.map,
        icon: this.options['icon']
    });
    this.run_id = 0;
    this.secperframe = 250;
    if (cssua.ua.mobile) {
        this.secperframe = 500;
    }

    google.maps.event.addListener(this.map, 'click', $.proxy(function(mouseEvent) {
        this.run(mouseEvent.latLng);
    }, this));
    // TODO: move window.initial_tracer into an option.
    google.maps.event.addListenerOnce(this.map, 'bounds_changed', $.proxy(function(){
        if (window.initial_tracer) {
            this.run(window.initial_tracer, true);
        }
    }, this));
    google.maps.event.addListener(this.map, 'center_changed', this.center_changed);
};

function oneDecimalPlace(x) {
    return Math.round(x*10)/10;
}

AdriftMap.prototype._update_history = function() {
    // This history js stuff should probably not be hardcoded in this class...
    // maybe a callback in this.options would be good.
    History.pushState({}, document.title, this.options['historyPageName'] + this.url_params());
};

AdriftMap.prototype._url_params = function() {
    return "?lat="+oneDecimalPlace(this.tracer.lat())+"&lng="+oneDecimalPlace(this.tracer.lng())+"&center="+oneDecimalPlace(this.map.getCenter().lng());
};

AdriftMap.prototype._run = function(latLng, dont_update_history) {

    this.tracer = latLng;
    var lat = Math.round(10 * this.tracer.lat()) / 10;
    var lng = Math.round(10 * this.tracer.lng()) / 10;

    // check if this is the first run and if we're  because 
    if (!dont_update_history) {
        this.update_history();
    }

    this.run_id++;
    this.marker.setPosition(latLng);
    var callback = function(data) {
        if (data.substring) {
            this.heatmap.setMap(null);
            notification(data, "error");
        } else if (data[0].length == 0) {
            // TODO: should this ever get called?
            this.heatmap.setMap(null);
            notification("You clicked on land, please click on the ocean", "error");
        } else {
            this.heatmap.setMap(null);
            this.heatMapData = data;
            this.draw_heat_map_data(0, this.run_id);
        }
    };

    // This endpoint also needs to be refactored out.
    $.getJSON(this.options['jsonEndpoint'] + "?lat="+lat+"&lng="+lng, $.proxy(callback, this));
};

AdriftMap.prototype._center_changed = function() {
    var newCenter = this.map.getCenter();
    var center_lon = oneDecimalPlace(((newCenter.lng()%360 + 540)%360 - 180));
    if (this.tracer) this.update_history();
    // Make sure we stay at the original center latitude.
    if (Math.abs(newCenter.lat()-this.options['center'].lat()) > 1e-4) {
        this.map.panTo(new google.maps.LatLng(this.options['center'].lat(), newCenter.lng()));
    }
};

AdriftMap.prototype._draw_heat_map_data = function(j, expected_run_id) {
    if (this.run_id != expected_run_id) return;
    if (j == 0) {
        for(var i = 0; i < this.heatMapData[j].length; i++) {
            var x = this.heatMapData[j][i].location;
            this.heatMapData[j][i].location = new google.maps.LatLng(x.lat, x.lng);
        }
        this.pointArray = new google.maps.MVCArray(this.heatMapData[j]);
        this.heatmap = new google.maps.visualization.HeatmapLayer({
            data: this.pointArray,
            radius: this.options['radius'],
            maxIntensity : 100,
            opacity : 1,
        });
        this.heatmap.setMap(this.map);
    } else {
        this.pointArray.clear();
        for(var i = 0; i < this.heatMapData[j].length; i++) {
            var x = this.heatMapData[j][i].location;
            y = new google.maps.LatLng(x.lat, x.lng)
            y.weight = this.heatMapData[j][i].weight; // what's this weight stuff? and why isn't it converted above?
            this.pointArray.push(y);
        }
    }
    var months = (j+1)*this.options['monthsPerFrame'];
    var years = Math.floor(months/12);
    months %= 12;

    // This set timeout is a hack to make it display at the same time as the heatmap.
    // I don't know why this works.
    setTimeout(function() {
        notification("Argo floats after " + years + " years and " + months + " months");
    }, 0);

    if (j + 1 < this.heatMapData.length) {
        setTimeout($.proxy(function() {
            this.draw_heat_map_data(j+1, expected_run_id);
        },this),this.secperframe);
    }
};
