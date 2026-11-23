"""Builds roomkaki.com/studio/ from the RightsAtlas Studio page (same engine, shared database).
Drops the RightsAtlas-only panels (Google search, e-mail subscribers), adds RoomKaki's Room actions panel.
  python studio/make_studio.py"""
import io
from pathlib import Path

SRC = Path(r"D:/rightsatlas/site/studio/index.html")
OUT = Path(__file__).resolve().parent / "index.html"
s = io.open(SRC, encoding="utf-8").read()
s = s.replace('"rightsatlas"', '"roomkaki"').replace("RightsAtlas Studio", "RoomKaki Studio").replace("RightsAtlas", "RoomKaki")
s = s.replace("loadGsc(d); loadPosts(d); loadSubs();", "loadPosts(d); loadRooms(d);")
old_card = ("'<div class=\"card\"><h2>Plays (films and songs)</h2>'+table(x.plays,[{h:\"Type\",k:\"kind\"},"
            "{h:\"Times\",k:\"n\",n:1},{h:\"Page\",k:\"path\",link:1}])+'</div>'+")
assert old_card in s, "plays card not found — RightsAtlas Studio changed"
s = s.replace(old_card, "'<div class=\"card\" id=\"actions\"><h2>Room actions</h2><p class=\"note\">Loading…</p></div>'+")
add = """
  // room actions: opens, out-clicks to source posts, alerts, searches + most-opened rooms
  function loadRooms(d){
    fetch(U.replace("studio_data","studio_room_actions"),{method:"POST",headers:{"apikey":K,"Authorization":"Bearer "+K,"Content-Type":"application/json"},body:JSON.stringify({p_site:"roomkaki",p_key:key,p_days:d})})
    .then(function(r){return r.json();}).then(function(a){
      var el=document.getElementById("actions"); if(!el||!a) return;
      var names={open:"Room opened",out:"Clicked to original post",alert:"Alert created",search:"Searched"};
      el.innerHTML='<h2>Room actions</h2>'+table((a.actions||[]).map(function(x){return {kind:names[x.kind]||x.kind,n:x.n};}),[{h:"Action",k:"kind"},{h:"Times",k:"n",n:1}])+
        '<h2 style="margin-top:12px">Most-opened rooms</h2>'+table(a.rooms,[{h:"Room",k:"title"},{h:"Opens",k:"opens",n:1}]);
    }).catch(function(){});
  }
"""
marker = "  // blog posts: how people read them"
assert marker in s
s = s.replace(marker, add + marker)
if "noindex" not in s:
    s = s.replace("<head>", '<head><meta name="robots" content="noindex,nofollow">', 1)
assert "studio_room_actions" in s and "loadGsc(d);" not in s and '"rightsatlas"' not in s
io.open(OUT, "w", encoding="utf-8", newline="").write(s)
print("studio page written:", OUT)
