<template>
  <div>
    <form @submit.prevent="updateNext">
      <div class="form-group">
        <label>
          {{ labels.nextChallenge }}
          <br />
          <small class="text-muted">{{ labels.challengeToRecommend }}</small>
        </label>
        <select class="form-control custom-select" v-model="selected_id">
          <option value="null">{{ labels.noneOption }}</option>
          <option
            v-for="challenge in otherChallenges"
            :value="challenge.id"
            :key="challenge.id"
          >
            {{ challenge.name }}
          </option>
        </select>
      </div>
      <div class="form-group">
        <button
          class="btn btn-success float-right"
          :disabled="!updateAvailable"
        >
          {{ labels.save }}
        </button>
      </div>
    </form>
  </div>
</template>

<script>
import CTFd from "../../compat/CTFd";

export default {
  props: {
    challenge_id: Number,
  },
  data: function () {
    return {
      challenge: null,
      challenges: [],
      selected_id: null,
      labels: {
        nextChallenge: _("Next Challenge"),
        challengeToRecommend: _(
          "Challenge to recommend after solving this challenge",
        ),
        noneOption: _("--"),
        save: _("Save"),
      },
    };
  },
  computed: {
    updateAvailable: function () {
      if (this.challenge) {
        return this.selected_id != this.challenge.next_id;
      } else {
        return false;
      }
    },
    // Get all challenges besides the current one and current next
    otherChallenges: function () {
      return this.challenges.filter((challenge) => {
        return challenge.id !== this.$props.challenge_id;
      });
    },
  },
  methods: {
    loadData: function () {
      CTFd.fetch(`/api/v1/challenges/${this.$props.challenge_id}`, {
        method: "GET",
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
          if (response.success) {
            this.challenge = response.data;
            this.selected_id = response.data.next_id;
          }
        });
    },
    loadChallenges: function () {
      CTFd.fetch("/api/v1/challenges?view=admin", {
        method: "GET",
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
          if (response.success) {
            this.challenges = response.data;
          }
        });
    },
    updateNext: function () {
      CTFd.fetch(`/api/v1/challenges/${this.$props.challenge_id}`, {
        method: "PATCH",
        credentials: "same-origin",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          next_id: this.selected_id != "null" ? this.selected_id : null,
        }),
      })
        .then((response) => {
          return response.json();
        })
        .then((data) => {
          if (data.success) {
            this.loadData();
            this.loadChallenges();
          }
        });
    },
  },
  created() {
    this.loadData();
    this.loadChallenges();
  },
};
</script>

<style scoped></style>
