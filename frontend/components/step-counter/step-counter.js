document.addEventListener("DOMContentLoaded", () => {
  let steps = 0;
  const stepGoal = 10000;

  console.log("Step Counter loaded");

  // Step Counter functions
  window.stepCounter = {
    getSteps() {
      return steps;
    },

    addSteps(amount) {
      steps += amount;
      console.log(`Steps: ${steps}/${stepGoal}`);
    },

    resetSteps() {
      steps = 0;
      console.log("Steps reset");
    }
  };
});