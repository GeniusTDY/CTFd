import{$ as t,p as d,C as i,y as u}from"./main-CYNmM_Fj.js";function r(l){let a=t("input[data-team-id]:checked").map(function(){return t(this).data("team-id")}),e=a.length===1?_("team"):_("teams");d({title:_("Delete Teams"),body:_("Are you sure you want to delete ")+a.length+" "+e+_("?"),success:function(){const o=[];for(var n of a)o.push(i.fetch(`/api/v1/teams/${n}`,{method:"DELETE"}));Promise.all(o).then(s=>{window.location.reload()})}})}function m(l){let a=t("input[data-team-id]:checked").map(function(){return t(this).data("team-id")});u({title:_("Edit Teams"),body:(()=>{const e={banned:_("Banned"),hidden:_("Hidden"),trueLabel:_("True"),falseLabel:_("False")};return t(`
    <form id="teams-bulk-edit">
      <div class="form-group">
        <label>${e.banned}</label>
        <select name="banned" data-initial="">
          <option value="">--</option>
          <option value="true">${e.trueLabel}</option>
          <option value="false">${e.falseLabel}</option>
        </select>
      </div>
      <div class="form-group">
        <label>${e.hidden}</label>
        <select name="hidden" data-initial="">
          <option value="">--</option>
          <option value="true">${e.trueLabel}</option>
          <option value="false">${e.falseLabel}</option>
        </select>
      </div>
    </form>
    `)})(),button:_("Submit"),success:function(){let e=t("#teams-bulk-edit").serializeJSON(!0);const o=[];for(var n of a)o.push(i.fetch(`/api/v1/teams/${n}`,{method:"PATCH",body:JSON.stringify(e)}));Promise.all(o).then(s=>{window.location.reload()})}})}t(()=>{t("#teams-delete-button").click(r),t("#teams-edit-button").click(m)});
