const create_room = document.getElementById('create-room');
const paste_link = document.getElementById('paste-link');
const join = document.getElementsByClassName('join');
const chatroomlink = document.getElementById('chatroomlink');
const homeurl = window.location.origin;
const copytoclipboard = document.getElementById('copytoclipboard');


const url = window.location.href;
const page = url.split('/')[1];
const side_btns = document.getElementsByClassName('side-button')

for (let el of side_btns){
    console.log(`sb-${page}`);
    if (el.id === `sb-${page}`){
        el.style.background = '#F9DB70';
    }
}



for (var i = 0; i < join.length; i++) {
        join[i].addEventListener('click', function (event){
            var el = event.target;
            el.setAttribute('href', el.getAttribute('videoroom'))
            el.click()
        })
    }

if(create_room)
{
    create_room.onclick = ()=> {
        $.ajax({
            type:"GET",
            url:"createroomlink/",
            success: function(result){
                if(result.valid)
                {
                    var link = homeurl+'/'+result.roomid;
                    chatroomlink.value = link;
                }   
                else{
                    chatroomlink.value = result.message;
                }         
            },
            error:function(result){
                console.error(result);
            }
        })
    };
}

if(chatroomlink && copytoclipboard)
{
    copytoclipboard.onclick = ()=>{
        navigator.clipboard.writeText(chatroomlink.value);
    };
}

