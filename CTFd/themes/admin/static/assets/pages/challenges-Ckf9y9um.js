import{$ as t,p as c,C as n,y as r}from"./main-DohPLd3T.js";function h(d){let i=t("input[data-challenge-id]:checked").map(function(){return t(this).data("challenge-id")}),a=i.length===1?_("challenge"):_("challenges");c({title:_("Delete Challenges"),body:_("Are you sure you want to delete ")+i.length+" "+a+_("?"),success:function(){const e=[];for(var l of i)e.push(n.fetch(`/api/v1/challenges/${l}`,{method:"DELETE"}));Promise.all(e).then(o=>{window.location.reload()})}})}function p(d){let i=t("input[data-challenge-id]:checked").map(function(){return t(this).data("challenge-id")}),a=t("input[data-challenge-id]:checked").map(function(){return t(this).data("solution-id")});r({title:_("Edit Challenges"),body:(()=>{const e={category:_("Category"),value:_("Value"),state:_("State"),solution:_("Solution"),visible:_("Visible"),hidden:_("Hidden"),solved:_("Solved")};return t(`
    <form id="challenges-bulk-edit">
      <div class="form-group">
        <label>${e.category}</label>
        <input type="text" name="category" data-initial="" value="">
      </div>
      <div class="form-group">
        <label>${e.value}</label>
        <input type="number" name="value" data-initial="" value="">
      </div>
      <div class="form-group">
        <label>${e.state}</label>
        <select name="state" data-initial="">
          <option value="">--</option>
          <option value="visible">${e.visible}</option>
          <option value="hidden">${e.hidden}</option>
        </select>
      </div>
      <div class="form-group">
        <label>${e.solution}</label>
        <select name="solution" data-initial="">
          <option value="">--</option>
          <option value="visible">${e.visible}</option>
          <option value="hidden">${e.hidden}</option>
          <option value="solved">${e.solved}</option>
        </select>
      </div>
    </form>
    `)})(),button:_("Submit"),success:function(){const e=[];let l=t("#challenges-bulk-edit").serializeJSON(!0),o={state:l.solution};if(delete l.solution,Object.keys(l).length!==0)for(var u of i)e.push(n.fetch(`/api/v1/challenges/${u}`,{method:"PATCH",body:JSON.stringify(l)}));if(o.state)for(var s of a)s&&e.push(n.fetch(`/api/v1/solutions/${s}`,{method:"PATCH",body:JSON.stringify(o)}));Promise.all(e).then(v=>{window.location.reload()})}})}t(()=>{t("#challenges-delete-button").click(h),t("#challenges-edit-button").click(p)});
