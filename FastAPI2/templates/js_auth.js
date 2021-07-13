function post(path, params, method='post') {

    // The rest of this code assumes you are not using a library.
    // It can be made less wordy if you use one.
    const form = document.createElement('form');
    form.method = method;
    form.action = path;
  
    for (const key in params) {
      if (params.hasOwnProperty(key)) {
        const hiddenField = document.createElement('input');
        hiddenField.type = 'hidden';
        hiddenField.name = key;
        hiddenField.value = params[key];
  
        form.appendChild(hiddenField);
      }
    }
  
    document.body.appendChild(form);
    form.submit();
  }
  
  function LoadPage(url,access_token){
    // /pages/{pagename}
    fetch(url,
    {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'accept': 'application/json',
            'Authorization': 'Bearer ' + access_token
        }
    })
    .then(response => {
        if( response.status === 200 ){
            return response.text();
        }else if( response.status === 401 ){
            alert("invalid token");
            throw new Error("invalid token");
        }
    })
    .then(text => {
        const doc = new DOMParser().parseFromString(text, "text/html");
        return doc;
    })
    .catch(err => {
        console.log("LoadPage fetch error:" + err);
    })
}

async function Refresh_token(url,refresh_token){
    return await fetch(url,
    {
        method: 'GET',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'accept': 'application/json',
            'Authorization': 'Bearer ' + refresh_token
        }
    })
    .then(response => {
        if( response.status === 200 ){
            return response.json();
        }else if( response.status === 401 ){
            alert("セッションが無効です。");
            sessionStorage.setItem("TOKEN","");    //セッションを空に
            sessionStorage.setItem("REFRESH_TOKEN","");    //セッションを空に
            sessionStorage.setItem("USERNAME","");    //セッションを空に
            throw new Error("リフレッシュトークンが違っています");
        }
    })
    .then(json => {
            retstr = JSON.parse(JSON.stringify(json));
            sessionStorage.setItem("TOKEN",retstr.access_token);    //セッションに保存
            sessionStorage.setItem("REFRESH_TOKEN",retstr.refresh_token);    //セッションに保存
            // sessionStorage.setItem("USERNAME",UserName);    //セッションに保存
            // location.href = "http://localhost:8000/userlist";
            // return LoadPage("http://localhost:8000/pages/test",retstr.access_token);
        })
    .catch(err => {
        console.log("refresh_token fetch error:" + err);
    })
}

function LoginClick(){
    // formを送るとリロードしちゃってtokenをキャンセルするので、ボタンクリックに変更した
    var loginForm = document.forms.loginForm;
    var UserName = loginForm.elements.UserName.value;
    var Password = loginForm.elements.Password.value;
    var msg = "username=" + UserName + "&password=" + Password;

    loginForm.elements.UserName.disabled = true;
    loginForm.elements.Password.disabled = true;
    loginForm.elements.submitbtn.disabled = true;
    var fetch_url = 'http://' + location.host + '/token';
    var post_url = 'http://' + location.host + '/pages/toppage' 

    fetch(fetch_url,
    {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'accept': 'application/json'
        },
        body: msg
    })
    .then(response => {
        if( response.status === 200 ){
            return response.json();
        }else if( response.status === 401 ){
            alert("ユーザかパスワードが間違っています");
            sessionStorage.setItem("TOKEN","");    //セッションを空に
            sessionStorage.setItem("REFRESH_TOKEN","");    //セッションを空に
            sessionStorage.setItem("USERNAME","");    //セッションを空に
            throw new Error("ユーザかパスワードが間違っています");
        }
    })
    .then(json => {
            retstr = JSON.parse(JSON.stringify(json));
            sessionStorage.setItem("TOKEN",retstr.access_token);    //セッションに保存
            sessionStorage.setItem("REFRESH_TOKEN",retstr.refresh_token);    //セッションに保存
            sessionStorage.setItem("USERNAME",UserName);    //セッションに保存
            // location.href = "http://localhost:8000/userlist";
            // return LoadPage("http://localhost:8000/pages/test",retstr.access_token);
            // post("http://localhost:8000/pages/test" + "?access_token=" + retstr.access_token,"");
            // post("http://localhost:8000/pages/sendpointtran" + "?access_token=" + retstr.access_token,"");
            post(post_url + "?access_token=" + retstr.access_token,"");
        })
    .catch(err => {
        console.log("formlogin fetch error:" + err);
        loginForm.elements.UserName.disabled = false;
        loginForm.elements.Password.disabled = false;
        loginForm.elements.submitbtn.disabled = false;
    })
}

async function ptcreate(data,token){
    var fetch_url = 'http://' + location.host + '/pt/create?access_token=';

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
    /* .then(json => {
            retstr = JSON.parse(JSON.stringify(json));
            alert("SendClick succeed");
            return json;
    })*/
    .catch(err => {
        console.log(err);
        return err;
    })
}

async function SendClick(){
    var SendPointtranForm = document.forms.SendPointtranForm;
    var FromUserName = SendPointtranForm.elements.fromusername.value;
    var ToUserName = SendPointtranForm.elements.tousername.value;
    var Point = SendPointtranForm.elements.point.value;
    var Comment = SendPointtranForm.elements.comment.value;

    document.getElementById("resultmessage").innerText = "";

    SendPointtranForm.elements.tousername.disabled = true;
    SendPointtranForm.elements.point.disabled = true;
    SendPointtranForm.elements.comment.disabled = true;

    var token = sessionStorage.getItem("TOKEN");

    let dateStr = new Date().toJSON();
    repl1 = dateStr.replace( /-/g ,"");
    repl2 = repl1.replace( /:/g ,"");
    repl3 = repl2.replace( /T/g ,"");
    dateStr = repl3.substring(0,14);

    data = {
        'from_user_name': FromUserName,
        'to_user_name': ToUserName,
        'entry_date': dateStr,
        'point': Point,
        'comment': Comment,
        'is_deleted': false
    }

    if (token === null) {
        alert("token is null");
        SendPointtranFormOpen();
        return
    }
    if ( ToUserName.trim().length == 0 ) {
        alert("tousername invalid");
        SendPointtranFormOpen();
        return
    } else 
    if ( Point == "") {
        alert("point invalid");
        SendPointtranFormOpen();
        return
    }
    (async() => {
        try{
            const ret1 = await ptcreate(data,sessionStorage.getItem("TOKEN"));
            if( ret1.errorcode === 0 || ret1.errorcode === 1 ){ /* 200-401 */
                document.getElementById("resultmessage").innerText = ret1.msg;
                document.getElementById("pointstock").value = ret1.newstock;
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
    SendPointtranForm.elements.tousername.value = "";
    SendPointtranForm.elements.point.value = "";
    SendPointtranForm.elements.comment.value = "";

    SendPointtranForm.elements.tousername.disabled = false;
    SendPointtranForm.elements.point.disabled = false;
    SendPointtranForm.elements.comment.disabled = false;
}

function SendPointtranFormOpen(){
    SendPointtranForm.elements.tousername.disabled = false;
    SendPointtranForm.elements.point.disabled = false;
    SendPointtranForm.elements.comment.disabled = false;
}

/* 未使用
function formLogin(){
    var loginForm = document.forms.loginForm;
    var UserName = loginForm.elements.UserName.value;
    var Password = loginForm.elements.Password.value;
    var msg = "username=" + UserName + "&password=" + Password;

    loginForm.elements.UserName.disabled = true;
    loginForm.elements.Password.disabled = true;
    loginForm.elements.submitbtn.disabled = true;

    fetch('http://localhost:8000/token',
    {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'accept': 'application/json'
        },
        body: msg
    })
    .then(response => {
        if( response.status === 200 ){
            return response.json();
        }else if( response.status === 401 ){
            alert("ユーザかパスワードが間違っています");
            sessionStorage.setItem("TOKEN","");    //セッションを空に
            throw new Error("ユーザかパスワードが間違っています");
        }
    })
    .then(json => {
            retstr = JSON.parse(JSON.stringify(json));
            sessionStorage.setItem("TOKEN",retstr.access_token);    //セッションに保存
            // alert("2nd:" + retstr.access_token);
        })
    .catch(err => console.log("formlogin fetch error:" + err))
} */

/* function formLogin_xhr(){
    var loginForm = document.forms.loginForm
    var UserName = loginForm.elements.UserName.value
    var Password = loginForm.elements.Password.value
    var xmlHttp = new XMLHttpRequest();

    xmlHttp.open('POST', "http://localhost:8000/token", true);
    xmlHttp.setRequestHeader("accept", "application/json");
    xmlHttp.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
    xmlHttp.send("username="+UserName +"&password="+ Password);
    
    xmlHttp.onload = function (event){
        if(xmlHttp.status === 200){
            alert(this.status + " succeeded")
            res = JSON.parse(xmlHttp.responseText);            
            sessionStorage.setItem("TOKEN",res.access_token);    //セッションに保存
        }else{
            alert(this.status + " error occured")
        }
    }
} */

function checkSessionStorage(){
    // var token = sessionStorage.getItem("TOKEN");
    // var username = sessionStorage.getItem("USERNAME");
    var token = sessionStorage.getItem("REFRESH_TOKEN");
    
        alert('sessionStorage refresh_token:' + token);
}

//Json形式のデータを送る
function postJson(url,param,proc) {
    var xmlHttp = new XMLHttpRequest();
    alert('postJson url:' + url + ' param:' + param );
    xmlHttp.open('POST', url, true);
    xmlHttp.setRequestHeader("accept", "application/json");
    xmlHttp.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
    // var p = JSON.stringify(param);
    // var p = "username=pirorino&password=password";
    //alert('username=pirorino&password=password : ' + param );
    xmlHttp.send(param);

    xmlHttp.onLoad = function (){
        if(xmlHttp.readyState === 4 && xmlHttp.status === 200){
            // alert("console out noparse:" + xmlHttp.responseText);
            proc(JSON.parse(xmlHttp.responseText));
            // alert("console out access_token:" + res.access_token);
        }
    }
}
//////////////予測入力
$(document).ready( function() {
    var token = sessionStorage.getItem("TOKEN");
    $("#tousername").autocomplete({
      source: function(req, resp){
          $.ajax({
              url: "http://"+ location.host + "/autocomplete-tousername?access_token=" + token + "&complete_str=" + req.term,
              type: "POST",
              cache: false,
              dataType: "json",
              /* data: {
              param1: req.term
              }, */
              success: function(o){
              resp(o);
              },
              error: function(xhr, ts, err){
              resp(['']);
              }
          });
      }
    });
  });//////////////////////////////////////ここからしたはゴミ

//Json形式のデータを受け取る
function getJson(url,token,proc) {
    var xmlHttp = new XMLHttpRequest();
    xmlHttp.open('GET', url, true);
    xmlHttp.setRequestHeader('Authorization', 'Bearer ' + token);
    xmlHttp.onreadystatechange = function (){
        if(this.readyState == 4){
            proc(JSON.parse(xmlHttp.response));
        }
    }
    xmlHttp.send();
}

//Token取得処理
function checkToken(){
    //セッションに保存済みか確認
    UserName = "pirorino"
    Password = "password"

    // sessionStorage.setItem("TOKEN","TEST");    //セッションに保存
    var token = sessionStorage.getItem("TOKEN");

    alert('start token:' + token);

    if(token != null){
        alert('token is not null or undefined');
        return;
    }else{
        location.href = "https://" + location.host + "/login"
    }
}    

function getToken(){
    //セッションに保存済みか確認
    UserName = "pirorino"
    Password = "password"

    // sessionStorage.setItem("TOKEN","TEST");    //セッションに保存
    var token = sessionStorage.getItem("TOKEN");
    var postJson_url = "http://" + location.host + "/token";

    alert('start token:' + token);

    if(token != null){
        alert('token is not null or undefined');
        return;
    }else{
    //tokenがないので取得する

    // var p = {};
    // location.search.substring(1).split('&').forEach(function(v){s=v.split('=');p[s[0]]=s[1];});
    //CODEが送られてきているか？
    // if(p.code != null && p.state == ClientStat){
        //パラメータがみっともないのでURLから取り除く
    //    history.replaceState(null,null,'?');    
        //トークンを取得
        // postJson("https://qiita.com/api/v2/access_tokens",  
        // alert('get Token:before postHTTP' + ClientSecret );

        postJson(postJson_url,"username=pirorino&password=password",
        // {client_id:"ClientID",client_secret:ClientSecret,code:p.code},
        function(e){
                sessionStorage.setItem("TOKEN",e.token);    //セッションに保存
                alert('Token:' + e.token );
                // func(e.token);                              //Token取得後の処理へ
            });
    // }else{//認証サイトへ遷移
    //    location.href = "https://localhost:8080/token?username="+
    //            UserName+"&password="+Password;
    // }       
    }
    return;
}

//ページが読み込まれた際に最初に呼び出される
function onLoad(){
    //トークンの要求
    var getJson_url = "http://" + location.host + "/users/me/";
    getToken(function(token){
        //トークンをテストするため、ユーザ情報を取得して表示
        getJson(getJson_url,token,function(r){
            var table = document.createElement('table');
            table.border = "1";
            Object.keys(r).forEach(function(key){
                var row = table.insertRow(-1);
                row.insertCell(-1).innerHTML = key;
                row.insertCell(-1).innerHTML = r[key];
            });
            document.body.appendChild(table);
        });
    });
}
