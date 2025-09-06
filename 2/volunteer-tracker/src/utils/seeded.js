export function hashStringToNumber(input) {
  let hash = 0
  for (let i = 0; i < input.length; i++) {
    hash = (hash << 5) - hash + input.charCodeAt(i)
    hash |= 0
  }
  return Math.abs(hash)
}

export function makeRng(seed) {
  let value = hashStringToNumber(String(seed)) || 1
  return () => {
    value ^= value << 13
    value ^= value >>> 17
    value ^= value << 5
    return ((value >>> 0) % 10000) / 10000
  }
}

export function pick(array, rnd) {
  return array[Math.floor((rnd ? rnd() : Math.random()) * array.length)]
}


