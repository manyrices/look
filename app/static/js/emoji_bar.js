;
(function($){
	$.fn.addEmoji = function(options){
		var defaults = {
			clomn : 8,
			emoji:['😀','😁','😂','🤣','😃','😄','😅','😆','😉','😊','😋','😎','😍','😘','😗','😙','😚','🙂','🤗','🤩','🤔','🤨','😐','😑','😶','🙄','😏','😣','😥','😮','🤐','😯','😪','😫','😴','😌','😛','😜','😝','🤤','😒','😓','😔','😕','🙃','🤑','😲','☹️','🙁','😖','😞','😟','😤','😢','😭','😦','😧','😨','🤯','😬','😰','😱','😳','🤪','😵','😡','😠','🤬','😷','🤒','🤕']
		};
		var options = $.extend({},defaults,options);
		this.each(function(){
			var area = $(this);
			var btn = $('<input type="button" value="😃" id="emojiBtn">');
			var tab = createTable();
			area.after(tab);
			tab.after(btn);
			$('td').click(function(){
				insertAtCursor(area, $(this).text())
			});
			$(document).bind('click',function(){
				$('#emojiTable').hide();
			});
			btn.bind('click', function(){
				event.stopPropagation();
				var bar = $('#emojiTable');
				bar.is(':hidden')?bar.show():bar.hide();
			});

			//创建emoji表格
			function createTable(){
				var table = $("<table id='emojiTable' style='display:none'></table>");
				var tr='<tr>';
				function createTr(res=0){
					for (var i=0; i < options.clomn; i++){
						var j = '';
						options.emoji[res]!= null ?j = options.emoji[res]:j='';
						var td = '<td>'+j+'</td>';
						res++;
						tr = tr+td;
					}
					tr = tr+'</tr>';
					if (res<options.emoji.length) {
						createTr(res);
					}
					return tr;
					
				}
				return table.html('<tbody>'+createTr()+'</tbody>');
			}
			//插入emoji到textarea
			function insertAtCursor(myField, myValue){	
		    	myField = myField.get(0);
		        //IE support
		        if (document.selection) 
		        {
		            myField.focus();
		            sel            = document.selection.createRange();
		            sel.text    = myValue;
		            sel.select();
		        }
		        //MOZILLA/NETSCAPE support
		        else if (myField.selectionStart || myField.selectionStart == '0') 
		        {
		            var startPos    = myField.selectionStart;
		            var endPos        = myField.selectionEnd;
		            // save scrollTop before insert
		            var restoreTop    = myField.scrollTop;
		            myField.value    = myField.value.substring(0, startPos) + myValue + myField.value.substring(endPos, myField.value.length);
		            if (restoreTop > 0)
		            {
		                // restore previous scrollTop
		                myField.scrollTop = restoreTop;
		            }
		            myField.focus();
		            myField.selectionStart    = startPos + myValue.length;
		            myField.selectionEnd    = startPos + myValue.length;
		        } else {
		            myField.value += myValue;
		            myField.focus();
		        }
		    }
		});
	}
})(window.jQuery);