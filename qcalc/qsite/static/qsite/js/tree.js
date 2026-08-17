// courtesy: https://bootsnipp.com/snippets/ypNAe
//$.fn.extend({
//    treed: function (o) {
$.fn.treed = function (o){
//      var openedClass = 'glyphicon-minus-sign';
//      var closedClass = 'glyphicon-plus-sign';
      var openedClass = 'icon-minus-circle2';
      var closedClass = 'icon-plus-circle2';

      if (typeof o != 'undefined'){
        if (typeof o.openedClass != 'undefined'){
        openedClass = o.openedClass;
        }
        if (typeof o.closedClass != 'undefined'){
        closedClass = o.closedClass;
        }
      };

        //initialize each of the top levels
        var tree = $(this);
        tree.addClass("tree");
        tree.find('li').has("ul").each(function () {
            var branch = $(this); //li with children ul
//            branch.prepend("<i class='indicator glyphicon " + closedClass + "'></i>");
            branch.prepend("<i class='indicator " + closedClass + "'></i>");
            branch.addClass('branch');
            branch.on('click', function (e) {
                if (this == e.target) {
                    var icon = $(this).children('i:first');
                    icon.toggleClass(openedClass + " " + closedClass);
                    $(this).children().children().toggle();
                    // Close all open nodes
                    $(this).siblings().not($(this)).each(function () {
                      $(this).children('i:first').removeClass(openedClass).addClass(closedClass);
                      $(this).children().children().hide();
                    });
                }
            })
            branch.children().children().toggle();
        });
        //fire event from the dynamically added icon
      tree.find('.branch .indicator').each(function(){
        $(this).on('click', function () {
            $(this).closest('li').click();
        });
      });
        //fire event to open branch if the li contains an anchor instead of text
        tree.find('.branch>a').each(function () {
            $(this).on('click', function (e) {
                $(this).closest('li').click();
                e.preventDefault();
            });
        });
        //fire event to open branch if the li contains a button instead of text
        tree.find('.branch>button').each(function () {
            $(this).on('click', function (e) {
                $(this).closest('li').click();
                e.preventDefault();
            });
        });
    };
//});
