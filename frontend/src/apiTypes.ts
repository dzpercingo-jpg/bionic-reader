export interface BionicSettings {
  enabled: boolean
  fixation_ratio: number
  min_word_length: number
  skip_short_words: boolean
  use_color_instead_of_bold: boolean
  prefix_color: string
  color_vowels: boolean
  vowel_color: string
  saccade_adaptive: boolean
  // v2 — council additions
  eye_anchor: boolean
  eye_anchor_color: string
  phrase_chunking: boolean
  phrase_chunk_size: number
  pos_coloring: boolean
  pos_color: string
}
