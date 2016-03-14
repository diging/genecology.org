
var app = angular.module('ConceptProfileSearchApp', ['ngResource']);

app.factory('ConceptProfile', function($resource) {
    return $resource('/concepts/:type.json', {
        type: "@type",
    }, {
        query: {
            method: 'GET',
            cache: true,
        }
    });
});



app.controller('ConceptProfileSearchController', ['$scope', 'ConceptProfile', function($scope, ConceptProfile) {
    $scope.profiles = [];
    $scope.query = '';
    $scope.nresults;
    $scope.nmax;
    $scope.page = 1;
    $scope.next = null;

    var element = angular.element($('#profile-results'));

    element.bind('scroll', function () {
        var raw = element[0];
        // Bottom of the element.
        if (raw.scrollTop + raw.offsetHeight == raw.scrollHeight) {
            $scope.extend();
        }
    });

    $scope.handleNext = function(data) {

        if (data.next) {
            $scope.next = $scope.page + 1;
        } else {
            $scope.next = null;
        }
    }

    $scope.search = function() {
        if ($scope.query.length > 2) {
            ConceptProfile.query({
                concept__label__icontains: $scope.query,
                type: $scope.profileType
            }).$promise.then(function(data){
                $scope.profiles = data.results;
                $scope.nresults = data.results.length;
                $scope.nmax = data.count;
                $scope.page = 1;
                $scope.handleNext(data);
            });

        // Default result set.
        } else if ($scope.query.length == 0) {
            ConceptProfile.query({
                type: $scope.profileType
            }).$promise.then(function(data){
                $scope.profiles = data.results;
                $scope.nresults = data.results.length;
                $scope.nmax = data.count;
                $scope.page = 1;
                $scope.handleNext(data);
            });
        }
    }

    $scope.extend = function() {
        if ($scope.next) {

            ConceptProfile.query({
                concept__label__icontains: $scope.query,
                type: $scope.profileType,
                page: $scope.next,
            }).$promise.then(function(data){
                data.results.forEach(function(result) {
                    $scope.profiles.push(result);
                })
                $scope.page += 1;
                $scope.nresults = $scope.profiles.length;
                $scope.nmax = data.count;
                $scope.handleNext(data);
            });
        }
    }
}]);
