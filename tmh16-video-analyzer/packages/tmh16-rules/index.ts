import { TMH16Card } from '../shared-types';

export interface EvidenceInput {
  hasPeak15: boolean;
  hasSeparateMovements: boolean;
  hasQueueEvidence: boolean;
  hasPedestrianObservations: boolean;
  hasSchoolObservations?: boolean;
  hasParkingObservations?: boolean;
  hasPublicTransportObservations?: boolean;
  hasServiceVehicleObservations?: boolean;
}

const status = (ok: boolean) => (ok ? 'complete' : 'incomplete') as const;

export function evaluateTMH16Alignment(input: EvidenceInput): TMH16Card[] {
  return [
    { topic: 'Peak 15-minute movement data', status: status(input.hasPeak15), note: 'Required for peak evidence.' },
    { topic: 'Separate movement reporting', status: status(input.hasSeparateMovements), note: 'Each stream/movement should be separate.' },
    { topic: 'Queue evidence', status: status(input.hasQueueEvidence), note: 'Estimated from tracked occupancy where needed.' },
    { topic: 'Pedestrian observations', status: status(input.hasPedestrianObservations), note: 'Crossings and exposure evidence.' },
    { topic: 'School observations', status: input.hasSchoolObservations === undefined ? 'not_applicable' : status(!!input.hasSchoolObservations), note: 'Drop-off/pick-up issues.' },
    { topic: 'Parking observations', status: input.hasParkingObservations === undefined ? 'not_applicable' : status(!!input.hasParkingObservations), note: 'Stopping/occupancy behavior.' },
    { topic: 'Public transport observations', status: input.hasPublicTransportObservations === undefined ? 'not_observed' : status(!!input.hasPublicTransportObservations), note: 'Taxi/bus interactions.' },
    { topic: 'Service/heavy vehicle observations', status: input.hasServiceVehicleObservations === undefined ? 'not_observed' : status(!!input.hasServiceVehicleObservations), note: 'Loading/service movements.' },
  ];
}
