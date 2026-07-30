import{$ as s,C as o,y as l}from"./main-DohPLd3T.js";const c={users:(e,a)=>o.api.patch_user_public({userId:e},a),teams:(e,a)=>o.api.patch_team_public({teamId:e},a)};function u(){const e=s(this),a=e.data("account-id"),n=e.data("state");let i;n==="visible"?i=!0:n==="hidden"&&(i=!1);const t={hidden:i};c[o.config.userMode](a,t).then(d=>{d.success&&(i?(e.data("state","hidden"),e.addClass("btn-danger").removeClass("btn-success"),e.text(_("Hidden"))):(e.data("state","visible"),e.addClass("btn-success").removeClass("btn-danger"),e.text(_("Visible"))))})}function r(e,a){const n={hidden:a==="hidden"},i=[];for(let t of e.accounts)i.push(c[o.config.userMode](t,n));for(let t of e.users)i.push(c.users(t,n));Promise.all(i).then(t=>{window.location.reload()})}function b(e){let a=s(".tab-pane.active input[data-account-id]:checked").map(function(){return s(this).data("account-id")}),n=s(".tab-pane.active input[data-user-id]:checked").map(function(){return s(this).data("user-id")}),i={accounts:a,users:n};l({title:_("Toggle Visibility"),body:(()=>{const t={visibility:_("Visibility"),visible:_("Visible"),hidden:_("Hidden")};return s(`
    <form id="scoreboard-bulk-edit">
      <div class="form-group">
        <label>${t.visibility}</label>
        <select name="visibility" data-initial="">
          <option value="">--</option>
          <option value="visible">${t.visible}</option>
          <option value="hidden">${t.hidden}</option>
        </select>
      </div>
    </form>
    `)})(),button:_("Submit"),success:function(){let d=s("#scoreboard-bulk-edit").serializeJSON(!0).visibility;r(i,d)}})}s(()=>{s(".scoreboard-toggle").click(u),s("#scoreboard-edit-button").click(b)});
