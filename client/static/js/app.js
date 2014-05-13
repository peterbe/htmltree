angular.module('htmltree', [
    'ngRoute',
    'classy'
])

.config(['$locationProvider', function ($locationProvider) {
    $locationProvider.html5Mode(true);
}])

.classy.controller({
    name: 'AppController',
    inject: ['$scope', '$http', '$location'],
    init: function() {
        //
        // makeTree('flare.json', '#tree');
        // this.$.url='http://www.peterbe.com';
        this.$.url = '';
        this.$.max_depth = 5;
        this.$.loading = false;
        this.$.page_width = 960;
        if (this.$location.search().url) {
            this.$.url = this.$location.search().url;
            this._drawTree(this.$location.search().url);
        }

    },

    submitForm: function() {
        this.$location.search('url', this.$.url);
        this._drawTree(this.$.url);
    },

    _drawTree: function(url) {
        this.$.loading = true;

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
            console.error(data);
            console.error('Status', status);
        })
        .finally(function() {
            this.$.loading = false;
        }.bind(this));
    },

})

;
