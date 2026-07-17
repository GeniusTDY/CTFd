<template>
  <div class="border-bottom">
    <div>
      <button
        type="button"
        class="close float-right"
        aria-label="Close"
        @click="deleteField()"
      >
        <span aria-hidden="true">&times;</span>
      </button>
    </div>

    <div class="row">
      <div class="col-md-3">
        <div class="form-group">
          <label>{{ labels.fieldType }}</label>
          <select
            class="form-control custom-select"
            v-model.lazy="field.field_type"
          >
            <option value="text">{{ labels.textField }}</option>
            <option value="boolean">{{ labels.checkbox }}</option>
          </select>
          <small class="form-text text-muted">{{ labels.fieldTypeHelp }}</small>
        </div>
      </div>
      <div class="col-md-9">
        <div class="form-group">
          <label>{{ labels.fieldName }}</label>
          <input type="text" class="form-control" v-model.lazy="field.name" />
          <small class="form-text text-muted">{{ labels.fieldNameHelp }}</small>
        </div>
      </div>

      <div class="col-md-12">
        <div class="form-group">
          <label>{{ labels.fieldDescription }}</label>
          <input
            type="text"
            class="form-control"
            v-model.lazy="field.description"
          />
          <small id="emailHelp" class="form-text text-muted">{{
            labels.fieldDescriptionHelp
          }}</small>
        </div>
      </div>

      <div class="col-md-12">
        <div class="form-check">
          <label class="form-check-label">
            <input
              class="form-check-input"
              type="checkbox"
              v-model.lazy="field.editable"
            />
            {{ labels.editableByUser }}
          </label>
        </div>
        <div class="form-check">
          <label class="form-check-label">
            <input
              class="form-check-input"
              type="checkbox"
              v-model.lazy="field.required"
            />
            {{ labels.requiredOnRegistration }}
          </label>
        </div>
        <div class="form-check">
          <label class="form-check-label">
            <input
              class="form-check-input"
              type="checkbox"
              v-model.lazy="field.public"
            />
            {{ labels.shownOnPublicProfile }}
          </label>
        </div>
      </div>
    </div>

    <div class="row pb-3">
      <div class="col-md-12">
        <div class="d-block">
          <button
            class="btn btn-sm btn-success btn-outlined float-right"
            type="button"
            @click="saveField()"
          >
            {{ labels.save }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import CTFd from "../../../compat/CTFd";
import { ezToast } from "../../../compat/ezq";

export default {
  props: {
    index: Number,
    initialField: Object,
  },
  data: function () {
    return {
      field: this.initialField,
      labels: {
        fieldType: _("Field Type"),
        textField: _("Text Field"),
        checkbox: _("Checkbox"),
        fieldTypeHelp: _("Type of field shown to the user"),
        fieldName: _("Field Name"),
        fieldNameHelp: _("Field name"),
        fieldDescription: _("Field Description"),
        fieldDescriptionHelp: _("Field Description"),
        editableByUser: _("Editable by user in profile"),
        requiredOnRegistration: _("Required on registration"),
        shownOnPublicProfile: _("Shown on public profile"),
        save: _("Save"),
      },
    };
  },
  methods: {
    persistedField: function () {
      // We're using Math.random() for unique IDs so new items have IDs < 1
      // Real items will have an ID > 1
      return this.field.id >= 1;
    },
    saveField: function () {
      let body = this.field;
      if (this.persistedField()) {
        CTFd.fetch(`/api/v1/configs/fields/${this.field.id}`, {
          method: "PATCH",
          credentials: "same-origin",
          headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
          },
          body: JSON.stringify(body),
        })
          .then((response) => {
            return response.json();
          })
          .then((response) => {
            if (response.success === true) {
              this.field = response.data;
              ezToast({
                title: _("Success"),
                body: _("Field has been updated!"),
                delay: 1000,
              });
            }
          });
      } else {
        CTFd.fetch(`/api/v1/configs/fields`, {
          method: "POST",
          credentials: "same-origin",
          headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
          },
          body: JSON.stringify(body),
        })
          .then((response) => {
            return response.json();
          })
          .then((response) => {
            if (response.success === true) {
              this.field = response.data;
              ezToast({
                title: _("Success"),
                body: _("Field has been created!"),
                delay: 1000,
              });
            }
          });
      }
    },
    deleteField: function () {
      if (confirm(_("Are you sure you'd like to delete this field?"))) {
        if (this.persistedField()) {
          CTFd.fetch(`/api/v1/configs/fields/${this.field.id}`, {
            method: "DELETE",
            credentials: "same-origin",
            headers: {
              Accept: "application/json",
              "Content-Type": "application/json",
            },
          })
            .then((response) => {
              return response.json();
            })
            .then((response) => {
              if (response.success === true) {
                this.$emit("remove-field", this.index);
              }
            });
        } else {
          this.$emit("remove-field", this.index);
        }
      }
    },
  },
};
</script>

<style scoped></style>
