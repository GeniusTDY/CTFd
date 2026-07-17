import{$ as e,u as d,C as n,B as u}from"./main-DmB-_ji2.js";function r(l){let t=e("input[data-team-id]:checked").map(function(){return e(this).data("team-id")}),o=t.length===1?_("team"):_("teams");d({title:_("Delete Teams"),body:_("Are you sure you want to delete ")+t.length+" "+o+_("?"),success:function(){const a=[];for(var i of t)a.push(n.fetch(`/api/v1/teams/${i}`,{method:"DELETE"}));Promise.all(a).then(s=>{window.location.reload()})}})}function m(l){let t=e("input[data-team-id]:checked").map(function(){return e(this).data("team-id")});u({title:_("Edit Teams"),body:e(`
    <form id="teams-bulk-edit">
      <div class="form-group">
        <label>${_("Banned")}</label>
        <select name="banned" data-initial="">
          <option value="">--</option>
          <option value="true">${_("True")}</option>
          <option value="false">${_("False")}</option>
        </select>
      </div>
      <div class="form-group">
        <label>${_("Hidden")}</label>
        <select name="hidden" data-initial="">
          <option value="">--</option>
          <option value="true">${_("True")}</option>
          <option value="false">${_("False")}</option>
        </select>
      </div>
    </form>
    `),button:_("Submit"),success:function(){let o=e("#teams-bulk-edit").serializeJSON(!0);const a=[];for(var i of t)a.push(n.fetch(`/api/v1/teams/${i}`,{method:"PATCH",body:JSON.stringify(o)}));Promise.all(a).then(s=>{window.location.reload()})}})}e(()=>{e("#teams-delete-button").click(r),e("#teams-edit-button").click(m)});
