function getNoRainItemComponent(timing) {
  return `
    <span class="material-symbols-outlined" style="
      --size: 2rem;
      color: cornflowerblue;
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

function getSmallRainItemComponent(timing) {
  return `
    <span class="material-symbols-outlined" style="
      --size: 1.25rem;
      color: cornflowerblue;
    ">humidity_high
    </span>
    <span>${timing}</span>
  `;
}

function getModerateRainItemComponent(timing) {
  return `
    <span class="material-symbols-outlined" style="
      --size: 1.25rem;
      color: cornflowerblue;
      position: absolute;
      left: 0.375rem;
      bottom: 0.875rem;
    ">humidity_high
    </span>
    <span class="material-symbols-outlined" style="
      --size: 0.875rem;
      color: cornflowerblue;
      position: absolute;
      top: 1rem;
      right: 0.5rem;
    ">humidity_high
    </span>
    <span>${timing}</span>
  `;
}

function getHeavyRainItemComponent(timing) {
  return `
    <span class="material-symbols-outlined" style="
      --size: 1.25rem;
      color: cornflowerblue;
      position: absolute;
      left: 0.125rem;
      bottom: 0.875rem;
    ">humidity_high
    </span>
    <span class="material-symbols-outlined" style="
      --size: 0.875rem;
      color: cornflowerblue;
      position: absolute;
      top: 1rem;
      right: 0.8125rem;
    ">humidity_high
    </span>
    <span class="material-symbols-outlined" style="
      --size: 1.25rem;
      color: cornflowerblue;
      position: absolute;
      right: 0.125rem;
      bottom: 0.875rem;
    ">humidity_high
    </span>
    <span>${timing}</span>
  `;
}