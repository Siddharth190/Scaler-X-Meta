# Meta Support Triage OpenEnv

## Problem
AI system to triage customer support tickets for Meta platforms.

## Setup
docker build -t meta-env .
docker run -p 7860:7860 meta-env

## Endpoints
/reset
/step
/state

## Live Demo
https://avenger190-scaler-x-meta.hf.space/ui/
