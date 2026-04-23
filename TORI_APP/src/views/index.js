import Boot from './Boot.js';
import System from './System.js';
import Pipeline from './Pipeline.js';
import Revenue from './Revenue.js';
import EventStream from './EventStream.js';
import Commands from './Commands.js';
import Projects from './Projects.js';
import Security from './Security.js';
import Monitoring from './Monitoring.js';
import Text from './Text.js';
import Voice from './Voice.js';
import Customization, { restoreCustomization } from './Customization.js';
import Portfolio from './Portfolio.js';
import Cognition from './Cognition.js';
import Roadmap from './Roadmap.js';

export { restoreCustomization };
export const views = {
  Boot, System, Pipeline, Revenue, Portfolio,
  EventStream, Commands, Projects,
  Cognition, Security, Monitoring, Text, Voice, Customization,
  Roadmap,
};
