const{useState,useEffect}=React,h=React.createElement;
const api=(p,o={})=>fetch('/api/'+p,{headers:{'Content-Type':'application/json'},...o}).then(async r=>{const d=await r.json();if(!r.ok)throw Error(d.error);return d});
function Login({onLogin}){const[f,setF]=useState({username:'',password:'',id:''}),[e,setE]=useState('');async function go(x){x.preventDefault();try{onLogin(await api('login',{method:'POST',body:JSON.stringify(f)}))}catch(z){setE(z.message)}}return h('div',{className:'login'},h('section',{className:'hero'},h('div',{className:'mark'},'Civitas'),h('div',null,h('h1',null,'Zeri juaj, ne vendimin e perbashket.'),h('p',null,'Platforme digjitale per kompani, institucione dhe biznese.'))),h('main',{className:'login-panel'},h('form',{className:'card',onSubmit:go},h('h2',null,'Hyrje e sigurt'),h('p',{className:'sub'},'Perdor kredencialet e autorizuara.'),[['username','Emri i perdoruesit','text'],['password','Fjalekalimi','password'],['id','ID identifikimi','text']].map(x=>h('label',{key:x[0]},x[1],h('input',{required:true,type:x[2],value:f[x[0]],onChange:q=>setF({...f,[x[0]]:q.target.value})}))),h('button',{className:'primary'},'Hyr ne platforme'),e&&h('div',{className:'error'},e))))}
function Home({u,go}){return h('section',null,h('div',{className:'eyebrow'},'Mire se erdhet'),h('h1',{className:'heading'},'Ballina'),h('p',{className:'lead'},u.name+', zgjidhni sherbimin qe deshironi te perdorni.'),h('div',{className:'grid'},...[['vote','Votimi','Merrni pjese ne vendim.'],['profile','Profili','Shihni te dhenat tuaja.'],['news','Te reja','Postoni tekst, foto, video ose file.'],['complaints','Ankesa','Dergo ankese te perdoruesit tjeter.']].map(x=>h('button',{className:'box home-card',onClick:()=>go(x[0]),key:x[0]},h('h3',null,x[1]),h('span',null,x[2])))))}
function Vote({u}){
 const[s,setS]=useState(10),[status,setStatus]=useState("active"),[r,setR]=useState({pro:0,kunder:0,abstenim:0}),[m,setM]=useState("");
 useEffect(()=>{
  const refresh=()=>api("votes").then(result=>{setR(result);setStatus(result.status||"active");});
  refresh();
  const clock=setInterval(()=>setS(x=>x>0?x-1:0),1000);
  const poller=setInterval(refresh,2000);
  return()=>{clearInterval(clock);clearInterval(poller);};
 },[]);
 async function cast(choice){
  if(status!=="active")return;
  try{const result=await api("votes",{method:"POST",body:JSON.stringify({username:u.username,choice:choice})});setR(result);setM("Vota juaj me peshe "+u.majority+" u ruajt me sukses.");}
  catch(error){setM(error.message);}
 }
 async function finish(){
  try{const result=await api("votes/finish",{method:"POST",body:JSON.stringify({username:u.username})});setR(result);setStatus("finished");setM(result.message);}
  catch(error){setM(error.message);}
 }
 const ended=status==="finished";
 return h("section",null,h("div",{className:"eyebrow"},"Vendimmarrje"),h("h1",{className:"heading"},ended?"Votimi perfundoi":"Votimi i hapur"),h("p",{className:"lead"},ended?"Rezultatet perfundimtare jane ruajtur.":"Vota e "+u.name+" numeron "+u.majority+" vota."),
  h("div",{className:"grid"},
   h("div",{className:"box"},h("h3",null,"Propozim: miratimi i planit"),h("div",{className:"timer"},"00:"+String(s).padStart(2,"0")),
    ended?h("div",{className:"notice"},"Votimi perfundoi per te gjithe perdoruesit."):
    h("div",null,h("div",{className:"choices"},h("button",{onClick:()=>cast("pro")},"Pro"),h("button",{onClick:()=>cast("kunder")},"Kunder"),h("button",{onClick:()=>cast("abstenim")},"Abstenim")),s===0&&u.username==="matinzeqiri"&&h("button",{className:"primary",onClick:finish},"Perfundo votimin")),
    m&&h("div",{className:"notice"},m)),
   h("div",{className:"box"},h("h3",null,ended?"Rezultatet perfundimtare":"Rezultatet aktuale"),h("div",{className:"results"},h("div",{className:"result"},"Pro",h("b",null,r.pro)),h("div",{className:"result"},"Kunder",h("b",null,r.kunder)),h("div",{className:"result"},"Abstenim",h("b",null,r.abstenim))))
  ));
}
function History(){
 const[rows,setRows]=useState([]);useEffect(()=>{api("vote-history").then(setRows)},[]);
 return h("section",null,h("div",{className:"eyebrow"},"Arkiva"),h("h1",{className:"heading"},"Historia e votimeve"),h("p",{className:"lead"},"Cdo votim i perfunduar ruhet me daten, oren dhe rezultatin e sakte."),
  h("div",{className:"posts"},rows.length?rows.map(row=>h("article",{className:"post",key:row.id},h("span",{className:"tag"},"Raundi #"+row.id),h("p",null,"Filloi: "+new Date(row.started_at).toLocaleString()),h("p",null,"Perfundoj: "+new Date(row.ended_at).toLocaleString()),h("div",{className:"results"},h("div",{className:"result"},"Pro",h("b",null,row.pro_total)),h("div",{className:"result"},"Kunder",h("b",null,row.kunder_total)),h("div",{className:"result"},"Abstenim",h("b",null,row.abstenim_total))))):h("div",{className:"notice"},"Ende nuk ka votime te perfunduara."))
 );
}
function Profile({u}){const data=[['Email',u.email],['Nr. tel',u.phone],['Vendbanimi',u.address],['Profesioni',u.profession],['Pozita',u.position],['Mazhoranca',u.majority+' vota']];return h('section',null,h('div',{className:'eyebrow'},'Llogaria ime'),h('h1',{className:'heading'},'Profili'),h('div',{className:'profile'},h('div',null,h('div',{className:'eyebrow',style:{color:'#b6d8cb'}},u.role),h('h2',null,u.name),h('span',null,'@'+u.username)),h('div',null,h('div',{className:'eyebrow',style:{color:'#b6d8cb'}},'Mazhoranca'),h('div',{className:'majority'},u.majority))),h('div',{className:'profile-data'},...data.map(x=>h('div',{className:'detail',key:x[0]},h('small',null,x[0]),h('strong',null,x[1])))))}
function Post({item}){
  let body=item.content;
  if(item.type==="image") body=h("img",{className:"media",src:item.content,alt:"Publikim"});
  else if(item.type==="video") body=h("video",{className:"media",src:item.content,controls:true});
  else if(item.type==="file") body=h("a",{href:item.content,target:"_blank"},"Hap file-in e ngarkuar");
  else if(item.type==="link"||/^https?:/.test(item.content)) body=h("a",{href:item.content,target:"_blank",rel:"noreferrer"},item.content);
  return h("article",{className:"post"},h("span",{className:"tag"},item.type+" - "+item.author),h("div",{className:"post-body"},body));
}
function News({u}){
  const[posts,setPosts]=useState([]);
  const[content,setContent]=useState("");
  const[type,setType]=useState("text");
  const[file,setFile]=useState(null);
  const[note,setNote]=useState("");
  const loadPosts=()=>api("posts").then(setPosts).catch(x=>setNote(x.message));
  useEffect(()=>{loadPosts()},[]);
  async function publish(event){
    event.preventDefault();
    try{
      if(type==="upload"){
        if(!file) throw Error("Zgjidhni nje file.");
        const form=new FormData();
        form.append("file",file);
        form.append("author",u.name);
        const response=await fetch("/api/upload",{method:"POST",body:form});
        const result=await response.json();
        if(!response.ok) throw Error(result.error);
      }else{
        await api("posts",{method:"POST",body:JSON.stringify({author:u.name,content:content,type:type})});
      }
      setContent(""); setFile(null); setNote("Publikimi u ruajt me sukses."); loadPosts();
    }catch(error){setNote(error.message);}
  }
  return h("section",null,
    h("div",{className:"eyebrow"},"Hapesire e perbashket"),
    h("h1",{className:"heading"},"Te reja"),
    h("p",{className:"lead"},"Ketu ruhen shkrime, linke, foto, video dhe file."),
    h("form",{className:"box feed-form",onSubmit:publish},
      h("select",{value:type,onChange:e=>setType(e.target.value)},
        h("option",{value:"text"},"Shkrim"),
        h("option",{value:"link"},"Lidhje / URL"),
        h("option",{value:"upload"},"Ngarko foto, video ose file")),
      type==="upload"
        ?h("input",{type:"file",onChange:e=>setFile(e.target.files[0])})
        :h("textarea",{required:true,rows:3,value:content,onChange:e=>setContent(e.target.value),placeholder:"Shkruani publikimin..."}),
      h("button",{className:"primary",type:"submit"},"Publiko"),
      note&&h("div",{className:"notice"},note)),
    h("div",{className:"posts"},posts.map(item=>h(Post,{item:item,key:item.id})))
  );
}
function Complaints({u}){const[rec,setRec]=useState(''),[m,setM]=useState(''),[rows,setRows]=useState([]),[note,setN]=useState('');const load=()=>api('complaints?user='+u.username).then(setRows);useEffect(load,[]);async function send(e){e.preventDefault();try{await api('complaints',{method:'POST',body:JSON.stringify({sender:u.username,recipient:rec,message:m})});setM('');setN('Ankesa u dergua.');load()}catch(x){setN(x.message)}}return h('section',null,h('div',{className:'eyebrow'},'Komunikim i drejtperdrejte'),h('h1',{className:'heading'},'Ankesa'),h('p',{className:'lead'},'Dergoni ankese te nje perdorues tjeter.'),h('form',{className:'box feed-form',onSubmit:send},h('select',{required:true,value:rec,onChange:e=>setRec(e.target.value)},h('option',{value:''},'Zgjidhni marresin'),...['omerzeqiri','matinzeqiri','nilzeqiri'].filter(x=>x!==u.username).map(x=>h('option',{value:x,key:x},x))),h('textarea',{required:true,rows:4,value:m,onChange:e=>setM(e.target.value),placeholder:'Shkruani ankesen tuaj...'}),h('button',{className:'primary'},'Dergo ankesen'),note&&h('div',{className:'notice'},note)),h('div',{className:'posts'},...rows.map(x=>h('article',{className:'post',key:x.id},h('span',{className:'tag'},x.sender+' -> '+x.recipient),h('p',null,x.message)))))}
function App(){
 const[u,setU]=useState(()=>JSON.parse(localStorage.getItem("civitas-user")||"null")),[p,setP]=useState("home");
 if(!u)return h(Login,{onLogin:x=>{localStorage.setItem("civitas-user",JSON.stringify(x));setU(x);setP("home")}});
 const V=p==="home"?Home:p==="vote"?Vote:p==="profile"?Profile:p==="news"?News:p==="history"?History:Complaints;
 const names={home:"Ballina",vote:"Votimi",profile:"Profili",news:"Te reja",complaints:"Ankesa",history:"Historia"};
 return h("div",{className:"app"},h("aside",{className:"side"},h("div",{className:"mark"},"Civitas"),h("nav",{className:"nav"},...["home","vote","profile","news","complaints","history"].map(x=>h("button",{type:"button",className:p===x?"active":"",onClick:()=>setP(x),key:x},names[x]))),h("button",{className:"logout",onClick:()=>{localStorage.removeItem("civitas-user");setU(null)}},"Dil")),h("main",{className:"main"},h(V,{u,go:setP})));
}ReactDOM.createRoot(document.getElementById("root")).render(h(App));
