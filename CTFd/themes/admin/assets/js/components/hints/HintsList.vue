<template>
  <div>
    <div>
      <HintCreationForm
        ref="HintCreationForm"
        :challenge_id="challenge_id"
        :hints="hints"
        @refreshHints="refreshHints"
      />
    </div>

    <div>
      <HintEditForm
        ref="HintEditForm"
        :challenge_id="challenge_id"
        :hint_id="editing_hint_id"
        :hints="hints"
        @refreshHints="refreshHints"
      />
    </div>

    <table class="table table-striped">
      <thead>
        <tr>
          <td class="text-center">
            <b>{{ labels.id }}</b>
          </td>
          <td class="text-center">
            <b>{{ labels.title }}</b>
          </td>
          <td class="text-center">
            <b>{{ labels.hint }}</b>
          </td>
          <td class="text-center">
            <b>{{ labels.cost }}</b>
          </td>
          <td class="text-center">
            <b>{{ labels.settings }}</b>
          </td>
        </tr>
      </thead>
      <tbody>
        <tr v-for="hint in hints" :key="hint.id">
          <td class="text-center">{{ hint.type }}</td>
          <td class="text-center">{{ hint.title }}</td>
          <td class="text-break">
            <pre>{{ hint.content }}</pre>
          </td>
          <td class="text-center">{{ hint.cost }}</td>
          <td class="text-center">
            <i
              role="button"
              class="btn-fa fas fa-edit"
              @click="editHint(hint.id)"
            ></i>
            <i
              role="button"
              class="btn-fa fas fa-times"
              @click="deleteHint(hint.id)"
            ></i>
          </td>
        </tr>
      </tbody>
    </table>
    <div class="col-md-12">
      <button class="btn btn-success float-right" @click="addHint">
        {{ labels.createHint }}
      </button>
    </div>
  </div>
</template>

<script>
import { ezQuery } from "../../compat/ezq";
import CTFd from "../../compat/CTFd";
import HintCreationForm from "./HintCreationForm.vue";
import HintEditForm from "./HintEditForm.vue";

export default {
  components: {
    HintCreationForm,
    HintEditForm,
  },
  props: {
    challenge_id: Number,
  },
  data: function () {
    return {
      hints: [],
      editing_hint_id: null,
      labels: {
        id: _("ID"),
        title: _("Title"),
        hint: _("Hint"),
        cost: _("Cost"),
        settings: _("Settings"),
        createHint: _("Create Hint"),
      },
    };
  },
  methods: {
    loadHints: async function () {
      let result = await CTFd.fetch(
        `/api/v1/challenges/${this.$props.challenge_id}/hints`,
        {
          method: "GET",
          credentials: "same-origin",
          headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
          },
        },
      );
      let response = await result.json();
      this.hints = response.data;
      return response.success;
    },
    addHint: function () {
      let modal = this.$refs.HintCreationForm.$el;
      $(modal).modal();
    },
    editHint: function (hintId) {
      this.editing_hint_id = hintId;
      let modal = this.$refs.HintEditForm.$el;
      $(modal).modal();
    },
    refreshHints: function (caller) {
      this.loadHints().then((success) => {
        if (success) {
          let modal;
          switch (caller) {
            case "HintCreationForm":
              modal = this.$refs.HintCreationForm.$el;
              console.log(modal);
              $(modal).modal("hide");
              break;
            case "HintEditForm":
              modal = this.$refs.HintEditForm.$el;
              $(modal).modal("hide");
              break;
            default:
              break;
          }
        } else {
          alert(
            _("An error occurred while updating this hint. Please try again."),
          );
        }
      });
    },
    deleteHint: function (hintId) {
      ezQuery({
        title: _("Delete Hint"),
        body: _("Are you sure you want to delete this hint?"),
        success: () => {
          CTFd.fetch(`/api/v1/hints/${hintId}`, {
            method: "DELETE",
          })
            .then((response) => {
              return response.json();
            })
            .then((data) => {
              if (data.success) {
                this.loadHints();
              }
            });
        },
      });
    },
  },
  created() {
    this.loadHints();
  },
};
</script>

<style scoped></style>
