import{$ as e,u as c,C as n,B as r}from"./main-DmB-_ji2.js";function h(d){let i=e("input[data-challenge-id]:checked").map(function(){return e(this).data("challenge-id")}),a=i.length===1?_("challenge"):_("challenges");c({title:_("Delete Challenges"),body:_("Are you sure you want to delete ")+i.length+" "+a+_("?"),success:function(){const t=[];for(var l of i)t.push(n.fetch(`/api/v1/challenges/${l}`,{method:"DELETE"}));Promise.all(t).then(o=>{window.location.reload()})}})}function p(d){let i=e("input[data-challenge-id]:checked").map(function(){return e(this).data("challenge-id")}),a=e("input[data-challenge-id]:checked").map(function(){return e(this).data("solution-id")});r({title:_("Edit Challenges"),body:e(`
    <form id="challenges-bulk-edit">
      <div class="form-group">
        <label>${_("Category")}</label>
        <input type="text" name="category" data-initial="" value="">
      </div>
      <div class="form-group">
        <label>${_("Value")}</label>
        <input type="number" name="value" data-initial="" value="">
      </div>
      <div class="form-group">
        <label>${_("State")}</label>
        <select name="state" data-initial="">
          <option value="">--</option>
          <option value="visible">${_("Visible")}</option>
          <option value="hidden">${_("Hidden")}</option>
        </select>
      </div>
      <div class="form-group">
        <label>${_("Solution")}</label>
        <select name="solution" data-initial="">
          <option value="">--</option>
          <option value="visible">${_("Visible")}</option>
          <option value="hidden">${_("Hidden")}</option>
          <option value="solved">${_("Solved")}</option>
        </select>
      </div>
    </form>
    `),button:_("Submit"),success:function(){const t=[];let l=e("#challenges-bulk-edit").serializeJSON(!0),o={state:l.solution};if(delete l.solution,Object.keys(l).length!==0)for(var u of i)t.push(n.fetch(`/api/v1/challenges/${u}`,{method:"PATCH",body:JSON.stringify(l)}));if(o.state)for(var s of a)s&&t.push(n.fetch(`/api/v1/solutions/${s}`,{method:"PATCH",body:JSON.stringify(o)}));Promise.all(t).then(g=>{window.location.reload()})}})}e(()=>{e("#challenges-delete-button").click(h),e("#challenges-edit-button").click(p)});
