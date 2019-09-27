#!/usr/bin/env ruby

require 'socket'

if ARGV.size == 0
  STDERR.puts "Usage: #$0 <number of clients>"
  exit 1
end

Integer(ARGV.shift).times do |n|
  fork do
    s = TCPSocket.new "localhost", 6666
    loop do
      s.puts "hello#{n}"
      s.gets "hello#{n}"
      sleep rand
      break if rand(100) == 50
    end
    s.close
  end
  sleep rand(0.005)
end
Process.wait
