interface Greeting { name: string; times: number }
const g: Greeting = { name: "world", times: 1 };
console.log(`hello ${g.name} x${g.times}`);
