export { initializeTelemetry, defaultConfig } from './config'
export type { TelemetryConfig } from './config'
export { createSpan, withSpan, addEvent, setAttributes, recordException } from './utils'
export type { TelemetryContext } from './utils'
