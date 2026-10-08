import { ref } from 'vue'
import { defineStore } from 'pinia'

export const useTransitionStore = defineStore('transition', () => {
  const selectedImgRect = ref(null)
  const selectedImgSrc = ref(null)

  const setRect = (rect, src = null) => {
    selectedImgRect.value = rect
    selectedImgSrc.value = src
  }

  return { selectedImgRect, selectedImgSrc, setRect }
})








