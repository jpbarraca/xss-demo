
$(document).ready(function(){
	$("#comment-authors").each(function(i, e){
		$.get( "/comment_authors", function( data ) {
			e.innerHTML = data;
		});

	});

});
