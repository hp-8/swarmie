import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import DeckDropzone from '../components/swarm/DeckDropzone.vue'

function makePdfFile(name = 'deck.pdf', sizeBytes = 1024 * 1024) {
  return new File(['x'.repeat(Math.min(sizeBytes, 100))], name, {
    type: 'application/pdf',
    lastModified: Date.now(),
  })
}

function makeFile(type = 'image/png', name = 'image.png', sizeBytes = 50000) {
  return new File(['x'.repeat(10)], name, { type, lastModified: Date.now() })
}

describe('DeckDropzone', () => {
  it('renders prompt UI when no file is set', () => {
    const wrapper = mount(DeckDropzone)
    expect(wrapper.find('.dz-prompt').exists()).toBe(true)
    expect(wrapper.find('.dz-file-info').exists()).toBe(false)
  })

  it('rejects non-PDF — sets dzError, does not emit file', async () => {
    const wrapper = mount(DeckDropzone)
    const file = makeFile('image/png', 'chart.png')

    // Trigger via onFileDrop by dispatching a fake drop event
    const dropEvent = new Event('drop', { bubbles: true })
    Object.defineProperty(dropEvent, 'dataTransfer', {
      value: { files: [file] },
    })
    await wrapper.find('.dropzone').trigger('drop', { dataTransfer: { files: [file] } })

    expect(wrapper.find('.dz-error-msg').exists()).toBe(true)
    expect(wrapper.find('.dz-error-msg').text()).toContain('PDF')
    expect(wrapper.emitted('update:file')).toBeFalsy()
  })

  it('rejects a file exceeding 25 MB', async () => {
    const wrapper = mount(DeckDropzone)
    // Create a File whose .size property reports >25MB
    const bigFile = new File(['x'], 'huge.pdf', { type: 'application/pdf' })
    Object.defineProperty(bigFile, 'size', { value: 26 * 1024 * 1024 })

    await wrapper.find('.dropzone').trigger('drop', { dataTransfer: { files: [bigFile] } })

    expect(wrapper.find('.dz-error-msg').exists()).toBe(true)
    expect(wrapper.find('.dz-error-msg').text()).toContain('25 MB')
    expect(wrapper.emitted('update:file')).toBeFalsy()
  })

  it('accepts a valid PDF under 25 MB and emits v-model:file', async () => {
    const wrapper = mount(DeckDropzone, {
      props: { 'onUpdate:file': (val) => wrapper.setProps({ file: val }) },
    })
    const pdfFile = makePdfFile('pitch.pdf', 2 * 1024 * 1024)

    await wrapper.find('.dropzone').trigger('drop', { dataTransfer: { files: [pdfFile] } })

    // No error shown
    expect(wrapper.find('.dz-error-msg').exists()).toBe(false)
    // v-model emitted
    expect(wrapper.emitted('update:file')).toBeTruthy()
    expect(wrapper.emitted('update:file')[0][0]).toBe(pdfFile)
  })

  it('shows file info panel after file is accepted', async () => {
    const pdfFile = makePdfFile('deck.pdf', 1024 * 500)
    const wrapper = mount(DeckDropzone, {
      props: { file: pdfFile },
    })
    expect(wrapper.find('.dz-file-info').exists()).toBe(true)
    expect(wrapper.find('.dz-filename').text()).toBe('deck.pdf')
  })

  it('clearDeck resets the file and hides file info', async () => {
    const pdfFile = makePdfFile('deck.pdf')
    const wrapper = mount(DeckDropzone, {
      props: { file: pdfFile },
    })
    await wrapper.find('.dz-clear').trigger('click')

    // emits null via update:file
    const emitted = wrapper.emitted('update:file')
    expect(emitted).toBeTruthy()
    expect(emitted[emitted.length - 1][0]).toBeNull()
  })

  it('clearDeck also clears dzError', async () => {
    const wrapper = mount(DeckDropzone)
    // First trigger an error
    await wrapper.find('.dropzone').trigger('drop', { dataTransfer: { files: [makeFile()] } })
    expect(wrapper.find('.dz-error-msg').exists()).toBe(true)

    // Now set a valid file so clear button is visible
    const pdfFile = makePdfFile()
    await wrapper.setProps({ file: pdfFile })
    await wrapper.find('.dz-clear').trigger('click')

    expect(wrapper.find('.dz-error-msg').exists()).toBe(false)
  })

  it('is disabled when disabled prop is true', () => {
    const wrapper = mount(DeckDropzone, { props: { disabled: true } })
    expect(wrapper.find('.dropzone').classes()).toContain('dz-disabled')
    expect(wrapper.find('.dropzone').attributes('aria-disabled')).toBe('true')
  })
})
