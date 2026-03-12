function getNoRainItemComponent(timing) {
  return `
    <span class="material-symbols-outlined" style="
      --size: 2rem;
      color: lightskyblue;
      position: relative;
    ">humidity_high
      <span style="
        content: '';
        position: absolute;
        top: 0.875rem;
        left: 0;
        width: 2rem;
        height: 0.25rem;
        rotate: 315deg;
        border-bottom: 2px solid darkgray;
        background-color: lightgray;
        display: block;
      "></span>
    </span>
    <span>${timing}</span>
  `;
}