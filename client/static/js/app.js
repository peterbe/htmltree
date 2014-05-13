angular.module('htmltree', [
    'ngRoute',
    'classy'
])

.config(['$locationProvider', function ($locationProvider) {
    $locationProvider.html5Mode(true);
}])

.classy.controller({
    name: 'AppController',
    inject: ['$scope', '$http', '$location', '$interval'],
    init: function() {
        //
        // makeTree('flare.json', '#tree');
        // this.$.url='http://www.peterbe.com';
        this.$.url = '';
        this.$.max_depth = 5;
        this.$.loading = false;
        this.$.page_width = 960;
        this.$.server_error = false;
        if (this.$location.search().url) {
            this.$.url = this.$location.search().url;
            this._drawTree(this.$location.search().url);
        }

        // this.$.jobs_in_queue = 0;
        // this.$interval(function() {
        //     this.$http.get('/tree')
        //     .success(function(r) {
        //         this.$.jobs_in_queue = r.jobs;
        //     }.bind(this));
        // }.bind(this), 1000);
    },

    submitForm: function() {
        if (this.$.url.trim()) {
            this.$location.search('url', this.$.url.trim());
            this._drawTree(this.$.url.trim());
        } else {
            d3.select('#tree svg').remove();
        }
    },

    _drawTree: function(url) {
        this.$.loading = true;
        this.$.server_error = false;
        this.$.page_width = window.innerWidth - 40;
        d3.select('#tree svg').remove();
        this.$http.post(
            '/tree',
            {url: url, max_depth: this.$.max_depth, treemap: true}
        )
        .success(function(response) {
            makeTree(response, '#tree', this.$.page_width);
            // makeTreemap(response, '#treemap', window.innerWidth - 40);
            // makeTreemap(response, '#treemap');
        }.bind(this))
        .error(function(data, status, headers) {
            if (status === 500) {
                this.$.server_error = true;
            }
            console.error(data);
            console.error('Status', status);
        }.bind(this))
        .finally(function() {
            this.$.loading = false;
        }.bind(this));
    },

    sampleSubmission: function(url) {
        this.$.url = url;
        this._drawTree(this.$.url.trim());
    }

})

;
