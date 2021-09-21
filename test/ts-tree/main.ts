import a from "b";

const b: ABC = 3;

interface SomeType {
  name: string;
  age: number;
  height: number | string;
}

export type OtherType = string;

function something<T, K>(abc: SomeType, qwerty: OtherType): Whatever {}

export function nothing<T, K>(abc: SomeType, qwerty: OtherType): Whatever {}

const c: SomeType<ABC> & OtherType = { name: "hello", age: 3, height: "5ft" };

qwerty(5, 4, 324);

something<SomeType[] | OtherType, string>(1, 2);

console.log(React < SomeType);

React.useState<SomeType[] | null>(null);

const b = () => {

};
