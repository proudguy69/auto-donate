<template>
  <div>
    <router-view></router-view>
    <div class="button"></div>
  </div>
</template>

<script>
  export default {
    methods: {
      button() {
        console.log('button clicked')
      }
    },
  }
</script>

<style>

body {
  margin: 0px;

  font-family: Arial, Helvetica, sans-serif;
}

</style>

