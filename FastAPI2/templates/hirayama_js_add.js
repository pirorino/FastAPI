async function OfferConversationClick(){
    var OfferConversationForm = document.forms.OfferConversationForm;

    var FromUserId = OfferConversationForm.elements.fromuserid.value;
    var ToUserId = OfferConversationForm.elements.touserid.value;
    var StartTimestamp = OfferConversationForm.elements.starttimestamp.value;
    var EndTimestamp = OfferConversationForm.elements.endtimestamp.value;

    document.getElementById("resultmessage").innerText = "";

    OfferConversationForm.elements.tousername.disabled = true;

    var token = sessionStorage.getItem("TOKEN");

    let dateStr = new Date().toJSON();
    repl1 = dateStr.replace( /-/g ,"");
    repl2 = repl1.replace( /:/g ,"");
    repl3 = repl2.replace( /T/g ,"");
    dateStr = repl3.substring(0,14);

    data = {
        'conversation_code': "",
        'user_id': FromUserId,
        'to_user_id': ToUserId,
        'start_timestamp': StartTimestamp,
        'scheduled_end_timestamp': EndTimestamp,
        'reservation_talking_category': "request",
        'is_deleted': false,
        'regist_timestamp': "",
        'regist_user_id': FromUserId,
        'update_timestamp': "",
        'update_user_id': 0,
        'version_id': 0
    }

    if (token === null) {
        alert("token is null");
        OfferConversationFormOpen();
        return
    }
    if ( ToUserName.trim().length == 0 ) {
        alert("tousername invalid");
        OfferConversationFormOpen();
        return
    } else 
    if ( StartTimestamp.trim().length == 0 ) {
        alert("StartTimestamp invalid");
        OfferConversationFormOpen();
        return
    } else 
    if ( ScheduledEndTimestamp.trim().length == 0 ) {
        alert("ScheduledEndTimestamp invalid");
        OfferConversationFormOpen();
        return
    }

    (async() => {
        try{
            const ret1 = await DoPost(data,sessionStorage.getItem("TOKEN"),'/users/ConversationListsCreate?access_token=');
            if( ret1.errorcode === 0 || ret1.errorcode === 1 ){ /* 200-401 */
                document.getElementById("resultmessage").innerText = ret1.msg;
                /* document.getElementById("pointstock").value = ret1.newstock; */
            } else if( ret1.errorcode === 2 ){
                url="http://" + location.host + "/refresh_token";
                const ret2 = await Refresh_token(url,sessionStorage.getItem("REFRESH_TOKEN"));
                const ret3 = await ptcreate(data,sessionStorage.getItem("TOKEN"));
                document.getElementById("resultmessage").innerText = ret3.msg;
            }
        }catch(e){
                alert("refresh_token error cought ");
        }
    })();
    OfferConversationForm.elements.tousername.value = "";
    OfferConversationForm.elements.tousername.disabled = false;
}

async function DoPost(data,token,posturl){
    var fetch_url = 'http://' + location.host + posturl;

    return await fetch(fetch_url + token,
    {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'accept': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        if( response.status === 200 ){
            return response.json();
        } else if (response.status === 401 ){
            return response.json();
        } else {
          throw new Error(response.json());
        }
    })
    .catch(err => {
        console.log(err);
        return err;
    })
}
