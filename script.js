window.clickShareBtn = function(){
    var clicked = false;
    Array.from(document.getElementsByTagName('div')).filter(function (item){
        if(item.getAttribute('role')=='dialog'){
            return true;
        }
    }).forEach(function (item){
        Array.from(item.getElementsByTagName('span')).filter(function (item){
            if(item.getAttribute('data-ad-rendering-role')=='share_button'){
                item.click();
                clicked = true;
            }
        })
    })
    return clicked;
}
window.clickGroupBtn = function(){
    var clicked = false;
    Array.from(document.getElementsByTagName('span')).forEach(function (item){
        if(item.innerHTML=='Group'){
            item.click();
            clicked = true;
        }
    })
    return clicked;
}
window.focusSearch = function(){
    var clicked = false;
    Array.from(document.getElementsByTagName('input')).forEach(function (item){
        if(item.getAttribute('placeholder')=='Search for groups'){
            item.focus();
            clicked = true;
        }
    })
    return clicked;
}
window.selectGroup = function(link){
    var groups = Array.from(document.getElementsByTagName('div')).filter(function (item){
        if(item.getAttribute('role')=='listitem' && item.getAttribute('data-visualcompletion')=='ignore-dynamic'){
            return true;
        }
    });
    try{
        if(groups[0].getElementsByTagName('a')[0].href.split('?')[0]==link){
            groups[0].getElementsByTagName('div')[0].click();
            return true;
        }
    }
    catch(e){}
    return false;
}
window.clickPostBtn = function(){
    var clicked = false;
    Array.from(document.getElementsByTagName('span')).forEach(function (item){
        if(item.innerHTML=='Post'){
            item.click();
            clicked = true;
        }
    })
    return clicked;
}

