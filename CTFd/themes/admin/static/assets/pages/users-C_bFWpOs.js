import{$ as t,p as r,C as a,y as u}from"./main-DohPLd3T.js";function d(l){let i=t("input[data-user-id]:checked").map(function(){return t(this).data("user-id")}),e=i.length===1?_("user"):_("users");r({title:_("Delete Users"),body:_("Are you sure you want to delete ")+i.length+" "+e+_("?"),success:function(){const o=[];for(var s of i)o.push(a.fetch(`/api/v1/users/${s}`,{method:"DELETE"}));Promise.all(o).then(n=>{window.location.reload()})}})}function c(l){let i=t("input[data-user-id]:checked").map(function(){return t(this).data("user-id")});u({title:_("Edit Users"),body:(()=>{const e={verified:_("Verified"),banned:_("Banned"),hidden:_("Hidden"),trueLabel:_("True"),falseLabel:_("False")};return t(`
    <form id="users-bulk-edit">
      <div class="form-group">
        <label>${e.verified}</label>
        <select name="verified" data-initial="">
          <option value="">--</option>
          <option value="true">${e.trueLabel}</option>
          <option value="false">${e.falseLabel}</option>
        </select>
      </div>
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
    `)})(),button:_("Submit"),success:function(){let e=t("#users-bulk-edit").serializeJSON(!0);const o=[];for(var s of i)o.push(a.fetch(`/api/v1/users/${s}`,{method:"PATCH",body:JSON.stringify(e)}));Promise.all(o).then(n=>{window.location.reload()})}})}t(()=>{t("#users-delete-button").click(d),t("#users-edit-button").click(c)});
